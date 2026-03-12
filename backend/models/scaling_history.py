"""
Historique des operations de scaling effectuees sur les VMs.
"""
from datetime import datetime
from .database import db


class ScalingHistory(db.Model):
    """Enregistre chaque evenement de scaling (up ou down)."""

    __tablename__ = "scaling_history"

    id = db.Column(db.Integer, primary_key=True)
    server_id   = db.Column(db.String(255), nullable=False, index=True)
    server_name = db.Column(db.String(255), nullable=True)
    direction   = db.Column(db.String(20),  nullable=False)   # scale_up / scale_down
    flavor_avant  = db.Column(db.String(100), nullable=True)
    flavor_apres  = db.Column(db.String(100), nullable=True)
    metrique      = db.Column(db.String(50),  nullable=True)   # cpu / ram / disk
    valeur_metrique = db.Column(db.Float,     nullable=True)   # ex: 90.0
    statut        = db.Column(db.String(20),  default="succes") # succes / echec
    message       = db.Column(db.Text,        nullable=True)
    timestamp     = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "server_id": self.server_id,
            "server_name": self.server_name,
            "direction": self.direction,
            "flavor_avant": self.flavor_avant,
            "flavor_apres": self.flavor_apres,
            "metrique": self.metrique,
            "valeur_metrique": self.valeur_metrique,
            "statut": self.statut,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
