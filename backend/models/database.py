"""
Initialisation de la base de donnees SQLite via SQLAlchemy.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """
    Initialise la base de donnees avec l'application Flask.
    Cree toutes les tables si elles n'existent pas.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
