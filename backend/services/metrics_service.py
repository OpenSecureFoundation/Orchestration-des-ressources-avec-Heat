"""
Service de collecte et traitement des metriques.
Recoit les donnees depuis les agents dans les VMs
et les diffuse via WebSocket.
"""

import logging
from datetime import datetime, timedelta

from backend.models.database import db
from backend.models.metric import Metric

logger = logging.getLogger(__name__)

# Reference vers l'instance SocketIO (injectee depuis app.py)
socketio_instance = None


def set_socketio(sio):
    """Injecte l'instance SocketIO pour l'emission d'evenements."""
    global socketio_instance
    socketio_instance = sio


class MetricsService:
    """Gestion de la collecte et du stockage des metriques."""

    @staticmethod
    def receive_metrics(data: dict) -> bool:
        """
        Recoit et enregistre les metriques depuis un agent VM.
        Emet les donnees via WebSocket aux clients connectes.
        Declenche la verification du scaling si une politique existe.
        """
        try:
            # Validation minimale des donnees recues
            server_id = data.get("server_id")
            if not server_id:
                logger.warning("Metriques recues sans server_id")
                return False

            # Resolution hostname -> UUID Nova si necessaire
            if not (len(server_id) == 36 and server_id.count("-") == 4):
                try:
                    from backend.services.openstack_service import OpenStackService
                    nc = OpenStackService.get_nova_client()
                    for s in nc.servers.list():
                        if s.name == server_id:
                            logger.info(f"Hostname resolved: {server_id} -> {s.id}")
                            server_id = s.id
                            data["server_id"] = s.id
                            break
                except Exception as e:
                    logger.debug(f"Resolution ignoree: {e}")

            network = data.get("network", {})

            # Enregistrement en base
            metrique = Metric(
                server_id=server_id,
                server_name=data.get("server_name", server_id),
                cpu_percent=data.get("cpu"),
                ram_percent=data.get("ram"),
                disk_percent=data.get("disk"),
                network_bytes_sent=network.get("bytes_sent"),
                network_bytes_recv=network.get("bytes_recv"),
                timestamp=datetime.utcnow(),
            )
            db.session.add(metrique)
            db.session.commit()

            # Emission WebSocket vers les clients abonnes
            if socketio_instance:
                socketio_instance.emit(
                    "metrics_update",
                    metrique.to_dict(),
                    room=server_id
                )

            # Declenchement de la verification scaling (import tardif pour eviter circulaire)
            try:
                from backend.services.scaling_service import ScalingService
                ScalingService.check_and_execute(server_id, data)
            except Exception as e:
                logger.debug(f"Verification scaling ignoree : {e}")

            logger.debug(
                f"Metriques recues pour '{server_id}' : "
                f"CPU={data.get('cpu')}% RAM={data.get('ram')}%"
            )
            return True

        except Exception as e:
            logger.error(f"Erreur enregistrement metriques : {e}")
            db.session.rollback()
            return False

    @staticmethod
    def get_metrics_history(server_id: str, hours: int = 24) -> list:
        """
        Recupere l'historique des metriques d'une VM.
        Limite aux 'hours' dernieres heures.
        """
        try:
            depuis = datetime.utcnow() - timedelta(hours=hours)
            metriques = (
                Metric.query
                .filter(
                    Metric.server_id == server_id,
                    Metric.timestamp >= depuis
                )
                .order_by(Metric.timestamp.asc())
                .all()
            )
            return [m.to_dict() for m in metriques]

        except Exception as e:
            logger.error(f"Erreur historique metriques '{server_id}' : {e}")
            return []

    @staticmethod
    def get_latest_metrics(server_id: str) -> dict:
        """Retourne la derniere metrique connue pour une VM."""
        try:
            metrique = (
                Metric.query
                .filter_by(server_id=server_id)
                .order_by(Metric.timestamp.desc())
                .first()
            )
            return metrique.to_dict() if metrique else {}

        except Exception as e:
            logger.error(f"Erreur derniere metrique '{server_id}' : {e}")
            return {}

    @staticmethod
    def get_all_servers_latest() -> list:
        """
        Retourne la derniere metrique de chaque VM connue.
        Utilise une sous-requete pour l'efficacite.
        """
        try:
            # Recupere les server_id distincts
            server_ids = db.session.query(Metric.server_id).distinct().all()
            resultats = []

            for (sid,) in server_ids:
                metrique = (
                    Metric.query
                    .filter_by(server_id=sid)
                    .order_by(Metric.timestamp.desc())
                    .first()
                )
                if metrique:
                    resultats.append(metrique.to_dict())

            return resultats

        except Exception as e:
            logger.error(f"Erreur metriques globales : {e}")
            return []

    @staticmethod
    def cleanup_old_metrics(days: int = 7) -> None:
        """Supprime les metriques plus anciennes que 'days' jours."""
        try:
            limite = datetime.utcnow() - timedelta(days=days)
            supprimees = Metric.query.filter(Metric.timestamp < limite).delete()
            db.session.commit()
            logger.info(f"Nettoyage metriques : {supprimees} enregistrements supprimes")
        except Exception as e:
            logger.error(f"Erreur nettoyage metriques : {e}")
            db.session.rollback()
