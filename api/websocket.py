"""
websocket.py
Responsabilité : Gestion des communications temps réel
entre le serveur et le dashboard via WebSocket.

C'est ce module qui fait que les graphiques du dashboard
se mettent à jour automatiquement sans recharger la page.
"""

import time
import logging
import threading
from flask_socketio import emit, join_room, leave_room

# ============================================================
# CONFIGURATION DU LOGGER
# ============================================================
logger = logging.getLogger("websocket")

# ============================================================
# ÉTAT DES CLIENTS CONNECTÉS
# ============================================================
_clients = {
    "connectes":  0,        # Nombre de clients actuellement connectés
    "historique": [],       # Liste des connexions/déconnexions
}

# Intervalle d'émission automatique des métriques (secondes)
EMISSION_INTERVAL = 5

# Référence vers le state global (injecté depuis adapter.py)
_state_ref    = None
_socketio_ref = None


# ============================================================
# INITIALISATION
# ============================================================
def initialiser(socketio, state: dict):
    """
    Initialise le module WebSocket avec les références
    vers SocketIO et le state global.

    Appelé une seule fois au démarrage depuis adapter.py.

    Paramètres :
        socketio : Instance Flask-SocketIO
        state    : Dict de l'état global de l'application
    """
    global _state_ref, _socketio_ref
    _state_ref    = state
    _socketio_ref = socketio

    # Enregistrement des événements WebSocket
    _enregistrer_evenements(socketio)

    # Démarrage du thread d'émission automatique
    _demarrer_emission_automatique()

    logger.info("Module WebSocket initialisé")


# ============================================================
# ENREGISTREMENT DES ÉVÉNEMENTS WEBSOCKET
# ============================================================
def _enregistrer_evenements(socketio):
    """
    Enregistre tous les événements WebSocket.
    Chaque @socketio.on() définit une réaction à un événement.
    """

    @socketio.on("connect")
    def on_connect():
        """
        Déclenché quand un client ouvre le dashboard.
        On lui envoie immédiatement les données actuelles.
        """
        _clients["connectes"] += 1
        _clients["historique"].append({
            "event": "connect",
            "time":  time.strftime("%H:%M:%S")
        })

        logger.info(
            f"Client connecté — "
            f"Total connectés : {_clients['connectes']}"
        )

        # Rejoindre la salle "dashboard"
        join_room("dashboard")

        # Envoyer immédiatement les données actuelles
        if _state_ref:
            emit("metrics_update", _construire_payload())
            emit("connection_ack", {
                "message":  "Connecté au dashboard Heat",
                "time":     time.strftime("%H:%M:%S"),
                "clients":  _clients["connectes"]
            })


    @socketio.on("disconnect")
    def on_disconnect():
        """Déclenché quand un client ferme le dashboard."""
        _clients["connectes"] = max(0, _clients["connectes"] - 1)
        _clients["historique"].append({
            "event": "disconnect",
            "time":  time.strftime("%H:%M:%S")
        })

        leave_room("dashboard")
        logger.info(
            f"Client déconnecté — "
            f"Total connectés : {_clients['connectes']}"
        )


    @socketio.on("demander_metriques")
    def on_demander_metriques():
        """
        Déclenché quand le frontend demande
        une mise à jour immédiate des métriques.
        """
        if _state_ref:
            emit("metrics_update", _construire_payload())
            logger.info("Métriques envoyées sur demande")


    @socketio.on("demander_logs")
    def on_demander_logs():
        """
        Déclenché quand le frontend demande
        les dernières entrées du journal.
        """
        if _state_ref:
            emit("logs_update", {
                "logs": _state_ref["logs"][:20]
            })


    @socketio.on("ping_serveur")
    def on_ping():
        """
        Permet au frontend de vérifier
        que la connexion est toujours active.
        """
        emit("pong_serveur", {
            "time":    time.strftime("%H:%M:%S"),
            "clients": _clients["connectes"]
        })


# ============================================================
# CONSTRUCTION DU PAYLOAD DE MÉTRIQUES
# ============================================================
def _construire_payload() -> dict:
    """
    Construit le dictionnaire de données envoyé
    au frontend à chaque mise à jour.
    """
    if not _state_ref:
        return {}

    vm       = _state_ref.get("vm",       {})
    policies = _state_ref.get("policies", {})
    stats    = _state_ref.get("stats",    {})
    logs     = _state_ref.get("logs",     [])

    return {
        # Métriques VM
        "cpu":           round(vm.get("cpu",  0), 1),
        "ram":           round(vm.get("ram",  0), 1),
        "flavor":        vm.get("current_flavor", "m1.small"),
        "vm_status":     vm.get("status",    "UNKNOWN"),
        "vm_name":       vm.get("name",      ""),
        "last_update":   vm.get("last_update", "--:--"),

        # Politiques actives
        "scale_up_threshold":   policies.get("scale_up_threshold",   80),
        "scale_down_threshold": policies.get("scale_down_threshold", 20),

        # Statistiques
        "stats": {
            "alertes_recues":   stats.get("alertes_recues",   0),
            "alertes_valides":  stats.get("alertes_valides",  0),
            "alertes_rejetees": stats.get("alertes_rejetees", 0),
            "scalings_up":      stats.get("scalings_up",      0),
            "scalings_down":    stats.get("scalings_down",    0),
        },

        # 5 dernières entrées du journal
        "logs": logs[:5],

        # Timestamp serveur
        "server_time": time.strftime("%H:%M:%S"),
    }


# ============================================================
# ÉMISSION AUTOMATIQUE (thread en arrière-plan)
# ============================================================
def _demarrer_emission_automatique():
    """
    Démarre un thread qui émet les métriques
    automatiquement toutes les EMISSION_INTERVAL secondes.

    Même si aucune alerte n'arrive des VMs,
    le dashboard se met quand même à jour régulièrement.
    """
    thread = threading.Thread(
        target=_boucle_emission,
        daemon=True,        # S'arrête quand l'app principale s'arrête
        name="websocket-emitter"
    )
    thread.start()
    logger.info(
        f"Émission automatique démarrée "
        f"(interval: {EMISSION_INTERVAL}s)"
    )


def _boucle_emission():
    """
    Boucle infinie qui émet les métriques périodiquement.
    Tourne dans un thread séparé.
    """
    while True:
        try:
            # N'émet que si des clients sont connectés
            if _clients["connectes"] > 0 and _state_ref and _socketio_ref:
                payload = _construire_payload()
                _socketio_ref.emit(
                    "metrics_update",
                    payload,
                    room="dashboard"
                )

        except Exception as e:
            logger.error(f"Erreur émission WebSocket : {e}")

        time.sleep(EMISSION_INTERVAL)


# ============================================================
# FONCTIONS D'ÉMISSION MANUELLE
# Appelées depuis adapter.py quand un événement important
# se produit (scaling, nouvelle alerte, etc.)
# ============================================================
def emettre_mise_a_jour():
    """
    Émet immédiatement une mise à jour des métriques.
    Appelé depuis adapter.py après chaque alerte reçue.
    """
    if not _socketio_ref or not _state_ref:
        return

    try:
        _socketio_ref.emit(
            "metrics_update",
            _construire_payload(),
            room="dashboard"
        )
    except Exception as e:
        logger.error(f"Erreur émission mise à jour : {e}")


def emettre_alerte_scaling(action: str, details: dict):
    """
    Émet une notification de scaling vers le dashboard.
    Affiche une notification visuelle dans l'interface.

    Paramètres :
        action  : "scale_up" ou "scale_down"
        details : Infos sur le scaling effectué
    """
    if not _socketio_ref:
        return

    try:
        _socketio_ref.emit(
            "scaling_event",
            {
                "action":         action,
                "ancien_flavor":  details.get("ancien_flavor"),
                "nouveau_flavor": details.get("nouveau_flavor"),
                "cpu":            details.get("cpu"),
                "time":           time.strftime("%H:%M:%S"),
                "message": (
                    f"Scale {'Up ▲' if action == 'scale_up' else 'Down ▼'} : "
                    f"{details.get('ancien_flavor')} → "
                    f"{details.get('nouveau_flavor')} "
                    f"(CPU: {details.get('cpu', 0):.0f}%)"
                )
            },
            room="dashboard"
        )
        logger.info(f"Événement scaling émis : {action}")

    except Exception as e:
        logger.error(f"Erreur émission scaling : {e}")


def emettre_notification(message: str, type_notif: str = "info"):
    """
    Émet une notification générale vers le dashboard.

    Paramètres :
        message    : Texte de la notification
        type_notif : "info", "success", "warning", "error"
    """
    if not _socketio_ref:
        return

    try:
        _socketio_ref.emit(
            "notification",
            {
                "message": message,
                "type":    type_notif,
                "time":    time.strftime("%H:%M:%S")
            },
            room="dashboard"
        )
    except Exception as e:
        logger.error(f"Erreur émission notification : {e}")


# ============================================================
# INFORMATIONS SUR LES CLIENTS
# ============================================================
def get_info_clients() -> dict:
    """
    Retourne les informations sur les clients connectés.
    Utile pour le monitoring.
    """
    return {
        "connectes":       _clients["connectes"],
        "emission_interval": EMISSION_INTERVAL,
        "derniers_events": _clients["historique"][-5:]
    }