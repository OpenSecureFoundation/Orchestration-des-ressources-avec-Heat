"""
Routes de gestion des metriques
Collecte, analyse et scaling automatique
"""

from flask import Blueprint, request
from backend.services.metrics_service import MetricsService
from backend.services.vm_service import VMService
from backend.models.metrics import Metric, ScalingPolicy
from backend.config import Config
from backend.utils.decorators import login_required
from backend.utils.helpers import success_response, error_response, log_action
from backend.models.database import Database

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/metrics')

@metrics_bp.route('/alert', methods=['POST'])
def receive_alert():
    """
    POST /api/metrics/alert
    Recevoir une alerte de metriques depuis un agent VM

    Body:
        {
            "source": "vm-name",
            "token": "secret-token",
            "timestamp": 1234567890,
            "cpu": 85.5,
            "ram": 60.2,
            "disk": 45.0,
            "network_in": 25.5,
            "network_out": 30.2,
            "network_latency": 15.3
        }
    """
    data = request.get_json()

    if not data:
        return error_response('Body JSON requis', 400)

    # Valider l'alerte
    validation = MetricsService.validate_alert(data, Config.SECRET_TOKEN)

    # Enregistrer l'alerte dans la base (meme si invalide pour audit)
    query = """
        INSERT INTO alerts (source, token_valid, metrics, is_valid, rejection_reason)
        VALUES (?, ?, ?, ?, ?)
    """

    from backend.models.database import json_to_db
    Database.execute_insert(
        query,
        (
            data.get('source'),
            validation['valid'],
            json_to_db(data),
            validation['valid'],
            validation['reason']
        )
    )

    if not validation['valid']:
        return error_response(validation['reason'], 400)

    source = data['source']
    metrics = validation['metrics']

    # Recuperer le serveur
    server_result = VMService.get_server(source)

    if not server_result['success']:
        return error_response(f'Serveur {source} non trouve', 404)

    server = server_result['server']

    # Sauvegarder les metriques
    MetricsService.save_metrics(server['id'], server['name'], metrics)

    # Determiner l'action de scaling
    scaling_decision = MetricsService.determine_scaling_action(server['id'], metrics)

    # Executer le scaling si necessaire
    if scaling_decision['action'] in ['scale_up', 'scale_down']:
        scaling_result = MetricsService.execute_scaling(
            server_id=server['id'],
            action=scaling_decision['action'],
            current_flavor=server['flavor']['name'],
            trigger_metric=scaling_decision['metric'],
            trigger_value=scaling_decision['value']
        )

        log_action(
            category='scaling',
            level='INFO' if scaling_result['success'] else 'WARNING',
            message=scaling_result['message'],
            details={
                'server': server['name'],
                'action': scaling_decision['action'],
                'old_flavor': server['flavor']['name'],
                'new_flavor': scaling_result.get('new_flavor')
            }
        )

        return success_response({
            'action': scaling_decision['action'],
            'message': scaling_result['message'],
            'new_flavor': scaling_result['new_flavor']
        })

    return success_response({
        'action': scaling_decision['action'],
        'message': scaling_decision['reason']
    })


@metrics_bp.route('/available', methods=['GET'])
@login_required
def get_available_metrics():
    """
    GET /api/metrics/available
    Lister les metriques disponibles et leur configuration
    """
    return success_response(Config.AVAILABLE_METRICS)


@metrics_bp.route('/history/<string:server_id>', methods=['GET'])
@login_required
def get_metrics_history(server_id):
    """
    GET /api/metrics/history/:server_id
    Recuperer l'historique des metriques d'un serveur

    Query params:
        ?metric_type=cpu&hours=24&limit=100
    """
    metric_type = request.args.get('metric_type', 'cpu')
    hours = int(request.args.get('hours', 24))
    limit = int(request.args.get('limit', 100))

    history = Metric.get_history(server_id, metric_type, hours, limit)

    return success_response(history)


@metrics_bp.route('/latest/<string:server_id>', methods=['GET'])
@login_required
def get_latest_metrics(server_id):
    """
    GET /api/metrics/latest/:server_id
    Recuperer les dernieres metriques d'un serveur
    """
    metrics = Metric.get_latest(server_id)

    return success_response(metrics)


@metrics_bp.route('/policies/<string:server_id>', methods=['GET'])
@login_required
def get_scaling_policy(server_id):
    """
    GET /api/metrics/policies/:server_id
    Recuperer la politique de scaling d'un serveur
    """
    policy = ScalingPolicy.get_by_server(server_id)

    if not policy:
        # Créer une politique par défaut si elle n'existe pas
        policy_id = ScalingPolicy.create_or_update(
            server_id=server_id,
            metric_type='cpu',
            scale_up_threshold=80,
            scale_down_threshold=20,
            cooldown_seconds=120,
            evaluation_periods=1,
            enabled=True
        )

        # Récupérer la politique créée
        policy = ScalingPolicy.get_by_server(server_id)

    return success_response(policy)


@metrics_bp.route('/policies/<string:server_id>', methods=['PUT'])
@login_required
def update_scaling_policy(server_id):
    """
    PUT /api/metrics/policies/:server_id
    Creer ou mettre a jour la politique de scaling

    Body:
        {
            "metric_type": "cpu",
            "scale_up_threshold": 80,
            "scale_down_threshold": 20,
            "cooldown_seconds": 120,
            "enabled": true
        }
    """
    data = request.get_json()

    if not data:
        return error_response('Body JSON requis', 400)

    # Valider les seuils
    if 'scale_up_threshold' in data and 'scale_down_threshold' in data:
        if data['scale_up_threshold'] <= data['scale_down_threshold']:
            return error_response(
                'Le seuil scale_up doit etre superieur a scale_down',
                400
            )

    # Valider le type de metrique
    if 'metric_type' in data:
        if data['metric_type'] not in Config.AVAILABLE_METRICS:
            return error_response(
                f'Type de metrique invalide: {data["metric_type"]}',
                400
            )

    policy_id = ScalingPolicy.create_or_update(
        server_id=server_id,
        metric_type=data.get('metric_type', 'cpu'),
        scale_up_threshold=data.get('scale_up_threshold', 80),
        scale_down_threshold=data.get('scale_down_threshold', 20),
        cooldown_seconds=data.get('cooldown_seconds', 120),
        evaluation_periods=data.get('evaluation_periods', 1),
        enabled=data.get('enabled', True)
    )

    log_action(
        user_id=request.current_user['id'],
        category='scaling',
        level='INFO',
        message=f'Politique de scaling mise a jour pour {server_id}'
    )

    return success_response({
        'policy_id': policy_id
    }, message='Politique mise a jour')


@metrics_bp.route('/policies/<string:server_id>/toggle', methods=['POST'])
@login_required
def toggle_scaling_policy(server_id):
    """
    POST /api/metrics/policies/:server_id/toggle
    Activer/desactiver une politique de scaling

    Body:
        {
            "enabled": true
        }
    """
    data = request.get_json()

    if 'enabled' not in data:
        return error_response('Champ enabled requis', 400)

    success = ScalingPolicy.toggle_enabled(server_id, data['enabled'])

    if not success:
        return error_response('Politique non trouvee', 404)

    log_action(
        user_id=request.current_user['id'],
        category='scaling',
        level='INFO',
        message=f'Politique {"activee" if data["enabled"] else "desactivee"} pour {server_id}'
    )

    return success_response(message='Politique mise a jour')


@metrics_bp.route('/scaling-events/<string:server_id>', methods=['GET'])
@login_required
def get_scaling_events(server_id):
    """
    GET /api/metrics/scaling-events/:server_id
    Recuperer l'historique des evenements de scaling

    Query params:
        ?limit=50
    """
    limit = int(request.args.get('limit', 50))

    events = ScalingPolicy.get_scaling_history(server_id, limit)

    return success_response(events)
