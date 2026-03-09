"""
Handlers WebSocket pour les mises a jour temps reel
Emet les metriques et evenements vers les clients connectes
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from backend.services.auth_service import AuthService
from backend.models.metrics import Metric, ScalingPolicy
from backend.services.vm_service import VMService
import threading
import time

socketio = SocketIO(cors_allowed_origins="*")

# Stockage des clients connectes par serveur
connected_clients = {}


def init_socketio(app):
    """
    Initialiser SocketIO avec l'application Flask

    Args:
        app: Instance Flask
    """
    socketio.init_app(app)

    # Demarrer le thread d'emission periodique
    thread = threading.Thread(target=emit_metrics_periodically, daemon=True)
    thread.start()


@socketio.on('connect')
def handle_connect():
    """
    Gestion de la connexion d'un client
    """
    print(f'Client connecte: {request.sid}')
    emit('connection_status', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """
    Gestion de la deconnexion d'un client
    """
    print(f'Client deconnecte: {request.sid}')

    # Retirer le client des rooms
    for server_id in list(connected_clients.keys()):
        if request.sid in connected_clients[server_id]:
            connected_clients[server_id].remove(request.sid)
            if not connected_clients[server_id]:
                del connected_clients[server_id]


@socketio.on('subscribe_server')
def handle_subscribe(data):
    """
    Inscription aux mises a jour d'un serveur specifique

    Args:
        data: {'server_id': 'xxx', 'session_token': 'yyy'}
    """
    if not data or 'server_id' not in data:
        emit('error', {'message': 'server_id requis'})
        return

    # Valider la session
    session_token = data.get('session_token')
    if session_token:
        user = AuthService.validate_session(session_token)
        if not user:
            emit('error', {'message': 'Session invalide'})
            return

    server_id = data['server_id']

    # Ajouter le client a la room du serveur
    join_room(f'server_{server_id}')

    # Tracker le client
    if server_id not in connected_clients:
        connected_clients[server_id] = []

    if request.sid not in connected_clients[server_id]:
        connected_clients[server_id].append(request.sid)

    print(f'Client {request.sid} inscrit au serveur {server_id}')

    # Envoyer immediatement les dernieres metriques
    send_latest_metrics(server_id)


@socketio.on('unsubscribe_server')
def handle_unsubscribe(data):
    """
    Desinscription des mises a jour d'un serveur

    Args:
        data: {'server_id': 'xxx'}
    """
    if not data or 'server_id' not in data:
        return

    server_id = data['server_id']

    # Retirer le client de la room
    leave_room(f'server_{server_id}')

    # Retirer du tracking
    if server_id in connected_clients and request.sid in connected_clients[server_id]:
        connected_clients[server_id].remove(request.sid)
        if not connected_clients[server_id]:
            del connected_clients[server_id]

    print(f'Client {request.sid} desinscrit du serveur {server_id}')


def send_latest_metrics(server_id):
    """
    Envoyer les dernieres metriques d'un serveur a tous les clients inscrits

    Args:
        server_id: ID du serveur
    """
    # Recuperer les dernieres metriques
    metrics = Metric.get_latest(server_id)

    # Recuperer les infos du serveur
    server_result = VMService.get_server(server_id)

    if not server_result['success']:
        return

    server = server_result['server']

    # Recuperer la politique de scaling
    policy = ScalingPolicy.get_by_server(server_id)

    # Recuperer les derniers evenements
    events = ScalingPolicy.get_scaling_history(server_id, limit=10)

    # Construire le payload
    payload = {
        'server_id': server_id,
        'server_name': server['name'],
        'server_status': server['status'],
        'flavor': server['flavor'],
        'metrics': {},
        'policy': policy,
        'recent_events': events,
        'timestamp': int(time.time())
    }

    # Organiser les metriques par type
    for metric in metrics:
        payload['metrics'][metric['metric_type']] = {
            'value': metric['value'],
            'unit': metric['unit'],
            'timestamp': metric['timestamp']
        }

    # Emettre vers tous les clients inscrits
    socketio.emit('metrics_update', payload, room=f'server_{server_id}')


def emit_metrics_periodically():
    """
    Thread daemon qui emet les metriques periodiquement
    Tourne toutes les 5 secondes
    """
    while True:
        time.sleep(5)

        # Emettre pour chaque serveur ayant des clients connectes
        for server_id in list(connected_clients.keys()):
            if connected_clients[server_id]:  # Si des clients sont connectes
                try:
                    send_latest_metrics(server_id)
                except Exception as e:
                    print(f'Erreur lors de l emission pour {server_id}: {str(e)}')


def broadcast_scaling_event(server_id, event_data):
    """
    Diffuser un evenement de scaling a tous les clients

    Args:
        server_id: ID du serveur
        event_data: Donnees de l'evenement
    """
    socketio.emit('scaling_event', event_data, room=f'server_{server_id}')


def broadcast_server_status_change(server_id, old_status, new_status):
    """
    Diffuser un changement de statut de serveur

    Args:
        server_id: ID du serveur
        old_status: Ancien statut
        new_status: Nouveau statut
    """
    socketio.emit('status_change', {
        'server_id': server_id,
        'old_status': old_status,
        'new_status': new_status,
        'timestamp': int(time.time())
    }, room=f'server_{server_id}')
