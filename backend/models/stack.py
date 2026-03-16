"""
Modele de donnees pour les stacks Heat.
"""

from datetime import datetime
from .database import db


class Stack(db.Model):
    """Represente une stack Heat deployee."""

    __tablename__ = "stacks"

    id = db.Column(db.Integer, primary_key=True)
    # Identifiant unique retourne par Heat
    heat_id = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(100), default="UNKNOWN")
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=True)
    parameters = db.Column(db.Text, nullable=True)  # JSON serialise
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialise le modele en dictionnaire."""
        return {
            "id": self.id,
            "heat_id": self.heat_id,
            "name": self.name,
            "status": self.status,
            "template_id": self.template_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
