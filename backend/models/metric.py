"""
Modele de donnees pour les metriques collectees depuis les VMs.
"""

from datetime import datetime
from .database import db


class Metric(db.Model):
    """Represente un enregistrement de metriques provenant d'une VM."""

    __tablename__ = "metrics"

    id = db.Column(db.Integer, primary_key=True)
    # Identifiant de la VM (Nova UUID ou hostname)
    server_id = db.Column(db.String(255), nullable=False, index=True)
    server_name = db.Column(db.String(255), nullable=True)
    # Metriques systeme
    cpu_percent = db.Column(db.Float, nullable=True)
    ram_percent = db.Column(db.Float, nullable=True)
    disk_percent = db.Column(db.Float, nullable=True)
    network_bytes_sent = db.Column(db.BigInteger, nullable=True)
    network_bytes_recv = db.Column(db.BigInteger, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        """Serialise le modele en dictionnaire."""
        return {
            "id": self.id,
            "server_id": self.server_id,
            "server_name": self.server_name,
            "cpu": self.cpu_percent,
            "ram": self.ram_percent,
            "disk": self.disk_percent,
            "network": {
                "bytes_sent": self.network_bytes_sent,
                "bytes_recv": self.network_bytes_recv,
            },
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
