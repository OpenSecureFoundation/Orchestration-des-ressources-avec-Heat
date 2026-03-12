"""
Modele de donnees pour les politiques de scaling automatique.
"""

from datetime import datetime
from .database import db


class ScalingPolicy(db.Model):
    """Definit les regles de scaling pour une VM donnee."""

    __tablename__ = "scaling_policies"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    server_name = db.Column(db.String(255), nullable=True)
    # Metrique surveillee : 'cpu', 'ram', 'disk'
    metric = db.Column(db.String(50), default="cpu")
    # Seuil en pourcentage declenchant le scale up
    threshold_up = db.Column(db.Float, default=80.0)
    # Seuil en pourcentage declenchant le scale down
    threshold_down = db.Column(db.Float, default=20.0)
    # Delai minimum entre deux operations de scaling (secondes)
    cooldown = db.Column(db.Integer, default=60)
    # Derniere operation de scaling
    last_scale_time = db.Column(db.DateTime, nullable=True)
    # Direction du dernier scaling : 'up' ou 'down'
    last_scale_direction = db.Column(db.String(10), nullable=True)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialise le modele en dictionnaire."""
        return {
            "id": self.id,
            "server_id": self.server_id,
            "server_name": self.server_name,
            "metric": self.metric,
            "threshold_up": self.threshold_up,
            "threshold_down": self.threshold_down,
            "cooldown": self.cooldown,
            "last_scale_time": (
                self.last_scale_time.isoformat() if self.last_scale_time else None
            ),
            "last_scale_direction": self.last_scale_direction,
            "enabled": self.enabled,
        }
