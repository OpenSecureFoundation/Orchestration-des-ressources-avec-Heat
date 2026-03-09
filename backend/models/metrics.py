"""
Modele Metrics - Gestion des metriques et politiques de scaling
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .database import Database

class Metric:
    """Modele pour gerer les metriques collectees"""

    @staticmethod
    def save(server_id: str, server_name: str, metric_type: str,
             value: float, unit: str, source: str = 'agent') -> int:
        """
        Sauvegarder une metrique

        Args:
            server_id: ID de la VM OpenStack
            server_name: Nom de la VM
            metric_type: Type de metrique (cpu, ram, disk, etc.)
            value: Valeur de la metrique
            unit: Unite de mesure
            source: Source de la metrique

        Returns:
            ID de la metrique sauvegardee
        """
        query = """
            INSERT INTO metrics
            (server_id, server_name, metric_type, value, unit, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        return Database.execute_insert(
            query,
            (server_id, server_name, metric_type, value, unit, source)
        )

    @staticmethod
    def get_latest(server_id: str, metric_type: str = None) -> List[Dict[str, Any]]:
        """
        Recuperer les dernieres metriques d'un serveur

        Args:
            server_id: ID du serveur
            metric_type: Type de metrique (None = toutes)
        """
        if metric_type:
            query = """
                SELECT * FROM metrics
                WHERE server_id = ? AND metric_type = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """
            return Database.execute_query(query, (server_id, metric_type))
        else:
            query = """
                SELECT m1.*
                FROM metrics m1
                INNER JOIN (
                    SELECT metric_type, MAX(timestamp) as max_timestamp
                    FROM metrics
                    WHERE server_id = ?
                    GROUP BY metric_type
                ) m2 ON m1.metric_type = m2.metric_type
                    AND m1.timestamp = m2.max_timestamp
                WHERE m1.server_id = ?
            """
            return Database.execute_query(query, (server_id, server_id))

    @staticmethod
    def get_history(server_id: str, metric_type: str,
                    hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Recuperer l'historique d'une metrique

        Args:
            server_id: ID du serveur
            metric_type: Type de metrique
            hours: Nombre d'heures d'historique
            limit: Nombre max de points
        """
        since = datetime.now() - timedelta(hours=hours)

        query = """
            SELECT * FROM metrics
            WHERE server_id = ? AND metric_type = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """

        return Database.execute_query(
            query,
            (server_id, metric_type, since.isoformat(), limit)
        )

    @staticmethod
    def cleanup_old_metrics(days: int = 7) -> int:
        """
        Nettoyer les anciennes metriques

        Args:
            days: Supprimer les metriques plus anciennes que X jours

        Returns:
            Nombre de metriques supprimees
        """
        cutoff = datetime.now() - timedelta(days=days)

        query = "DELETE FROM metrics WHERE timestamp < ?"

        return Database.execute_update(query, (cutoff.isoformat(),))


class ScalingPolicy:
    """Modele pour gerer les politiques de scaling"""

    @staticmethod
    def create_or_update(server_id: str, metric_type: str,
                        scale_up_threshold: float, scale_down_threshold: float,
                        cooldown_seconds: int = 120, evaluation_periods: int = 1,
                        enabled: bool = True) -> int:
        """
        Creer ou mettre a jour une politique de scaling

        Returns:
            ID de la politique
        """
        # Verifier si la politique existe
        existing = ScalingPolicy.get_by_server(server_id)

        if existing:
            # Mise a jour
            query = """
                UPDATE scaling_policies
                SET metric_type = ?, scale_up_threshold = ?, scale_down_threshold = ?,
                    cooldown_seconds = ?, evaluation_periods = ?, enabled = ?,
                    updated_at = ?
                WHERE server_id = ?
            """
            Database.execute_update(
                query,
                (metric_type, scale_up_threshold, scale_down_threshold,
                 cooldown_seconds, evaluation_periods, enabled,
                 datetime.now().isoformat(), server_id)
            )
            return existing['id']
        else:
            # Creation
            query = """
                INSERT INTO scaling_policies
                (server_id, metric_type, scale_up_threshold, scale_down_threshold,
                 cooldown_seconds, evaluation_periods, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            return Database.execute_insert(
                query,
                (server_id, metric_type, scale_up_threshold, scale_down_threshold,
                 cooldown_seconds, evaluation_periods, enabled)
            )

    @staticmethod
    def get_by_server(server_id: str) -> Optional[Dict[str, Any]]:
        """Recuperer la politique de scaling d'un serveur"""
        query = "SELECT * FROM scaling_policies WHERE server_id = ?"
        policies = Database.execute_query(query, (server_id,))
        return policies[0] if policies else None

    @staticmethod
    def get_all_enabled() -> List[Dict[str, Any]]:
        """Recuperer toutes les politiques actives"""
        query = "SELECT * FROM scaling_policies WHERE enabled = 1"
        return Database.execute_query(query)

    @staticmethod
    def toggle_enabled(server_id: str, enabled: bool) -> bool:
        """Activer/desactiver une politique"""
        query = """
            UPDATE scaling_policies
            SET enabled = ?, updated_at = ?
            WHERE server_id = ?
        """
        rows_affected = Database.execute_update(
            query,
            (enabled, datetime.now().isoformat(), server_id)
        )
        return rows_affected > 0

    @staticmethod
    def log_scaling_event(server_id: str, event_type: str, old_flavor: str = None,
                         new_flavor: str = None, trigger_metric: str = None,
                         trigger_value: float = None, success: bool = True,
                         message: str = None) -> int:
        """
        Enregistrer un evenement de scaling

        Args:
            server_id: ID du serveur
            event_type: Type ('scale_up', 'scale_down', 'cooldown', 'rejected')
            old_flavor: Ancien flavor
            new_flavor: Nouveau flavor
            trigger_metric: Metrique qui a declenche
            trigger_value: Valeur de la metrique
            success: Succes de l'operation
            message: Message descriptif

        Returns:
            ID de l'evenement
        """
        query = """
            INSERT INTO scaling_events
            (server_id, event_type, old_flavor, new_flavor, trigger_metric,
             trigger_value, success, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        return Database.execute_insert(
            query,
            (server_id, event_type, old_flavor, new_flavor, trigger_metric,
             trigger_value, success, message)
        )

    @staticmethod
    def get_scaling_history(server_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Recuperer l'historique des evenements de scaling"""
        query = """
            SELECT * FROM scaling_events
            WHERE server_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        return Database.execute_query(query, (server_id, limit))

    @staticmethod
    def get_last_scaling_event(server_id: str) -> Optional[Dict[str, Any]]:
        """Recuperer le dernier evenement de scaling (pour cooldown)"""
        query = """
            SELECT * FROM scaling_events
            WHERE server_id = ? AND event_type IN ('scale_up', 'scale_down')
            ORDER BY timestamp DESC
            LIMIT 1
        """
        events = Database.execute_query(query, (server_id,))
        return events[0] if events else None
