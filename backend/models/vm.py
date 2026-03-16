"""
Modele de donnees pour les machines virtuelles.
"""

from datetime import datetime
from .database import db


class VM(db.Model):
    """Represente une machine virtuelle Nova."""

    __tablename__ = "vms"

    id = db.Column(db.Integer, primary_key=True)
    # Identifiant Nova (UUID)
    nova_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(100), default="UNKNOWN")
    flavor = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    stack_id = db.Column(db.Integer, db.ForeignKey("stacks.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialise le modele en dictionnaire."""
        return {
            "id": self.id,
            "nova_id": self.nova_id,
            "name": self.name,
            "status": self.status,
            "flavor": self.flavor,
            "ip_address": self.ip_address,
            "stack_id": self.stack_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
