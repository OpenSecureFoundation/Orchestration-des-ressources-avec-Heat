"""
Modele de donnees pour les templates Heat.
"""

from datetime import datetime
from .database import db


class Template(db.Model):
    """Represente un template Heat stocke dans la base de donnees."""

    __tablename__ = "templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    # Chemin vers le fichier YAML sur le disque
    file_path = db.Column(db.String(500), nullable=False)
    # 'builtin' ou 'user'
    category = db.Column(db.String(50), default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialise le modele en dictionnaire."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "file_path": self.file_path,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
