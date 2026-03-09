"""
Application Flask principale
Initialise tous les composants et enregistre les blueprints
"""

from flask import Flask
from flask_cors import CORS
from backend.config import Config
from backend.models.database import Database
from backend.websocket.handlers import init_socketio
import os

def create_app():
    """
    Factory pour creer l'application Flask

    Returns:
        Instance Flask configuree
    """
    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
    )

    # Configuration
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # CORS
    CORS(app)

    # Valider la configuration OpenStack
    try:
        Config.validate()
    except ValueError as e:
        print(f"ATTENTION: {str(e)}")
        print("L'application peut fonctionner en mode limite sans OpenStack")

    # Initialiser la base de donnees
    Database.initialize(Config.DATABASE_PATH)

    # Creer les dossiers necessaires
    os.makedirs(Config.USER_TEMPLATES_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)

    # Enregistrer les blueprints (routes)
    from backend.routes import (
        auth_bp,
        template_bp,
        stack_bp,
        vm_bp,
        metrics_bp,
        dashboard_bp
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(stack_bp)
    app.register_blueprint(vm_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(dashboard_bp)

    # Initialiser WebSocket
    init_socketio(app)

    # Route de test
    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'Application fonctionnelle'}

    return app
