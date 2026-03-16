"""
Application Flask principale.
Initialise tous les composants : BDD, SocketIO, routes, templates builtin.
"""

import logging
import os
from flask import Flask
from flask_socketio import SocketIO, join_room, leave_room

from backend.config import Config
from backend.models.database import init_db
from backend.models.template import Template
from backend.models.database import db
from backend.routes import main_bp, stack_bp, vm_bp, metrics_bp, template_bp
from backend.services.metrics_service import set_socketio

logger = logging.getLogger(__name__)

# Instance SocketIO globale (accessible depuis les services)
socketio = SocketIO()


def create_app() -> Flask:
    """
    Fabrique d'application Flask.
    Configure et retourne l'instance Flask prete a l'emploi.
    """
    # Configuration du logging en premier
    Config.setup_logging()
    Config.validate()

    app = Flask(
        __name__,
        template_folder=os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "frontend", "templates"
        ),
        static_folder=os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "frontend", "static"
        ),
    )

    # Configuration Flask
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 Mo max upload

    # Initialisation base de donnees
    init_db(app)

    # Initialisation SocketIO
    socketio.init_app(
        app,
        async_mode="eventlet",
        cors_allowed_origins="*",
        logger=False,
        engineio_logger=False,
    )

    # Injection de SocketIO dans le service de metriques
    set_socketio(socketio)

    # Enregistrement des blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(stack_bp)
    app.register_blueprint(vm_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(template_bp)

    # Chargement des templates builtin au demarrage
    with app.app_context():
        _charger_templates_builtin()

    logger.info("Application Flask initialisee avec succes")
    return app


def _charger_templates_builtin() -> None:
    """
    Enregistre les templates builtin dans la base de donnees
    s'ils n'existent pas encore.
    """
    templates_builtin = [
        {
            "name": "Stack Complete",
            "description": (
                "Stack complete avec reseau prive, security group, "
                "VM Ubuntu 22.04 et agent de metriques"
            ),
            "file_path": str(Config.TEMPLATES_BUILTIN_DIR / "main_stack.yaml"),
            "category": "builtin",
        },
        {
            "name": "Template Reseau",
            "description": "Cree un reseau prive avec subnet et routeur",
            "file_path": str(Config.TEMPLATES_BUILTIN_DIR / "network_template.yaml"),
            "category": "builtin",
        },
        {
            "name": "Template VM",
            "description": "Deploie une VM avec agent de metriques",
            "file_path": str(Config.TEMPLATES_BUILTIN_DIR / "vm_template.yaml"),
            "category": "builtin",
        },
    ]

    for t_data in templates_builtin:
        # Seulement si le fichier existe et n'est pas encore en base
        if os.path.exists(t_data["file_path"]):
            existant = Template.query.filter_by(name=t_data["name"]).first()
            if not existant:
                template = Template(**t_data)
                db.session.add(template)
                logger.info(f"Template builtin charge : {t_data['name']}")

    try:
        db.session.commit()
    except Exception as e:
        logger.warning(f"Erreur chargement templates builtin : {e}")
        db.session.rollback()


# ---- Evenements WebSocket ----

@socketio.on("connect")
def on_connect():
    """Client WebSocket connecte."""
    logger.debug("Client WebSocket connecte")


@socketio.on("disconnect")
def on_disconnect():
    """Client WebSocket deconnecte."""
    logger.debug("Client WebSocket deconnecte")


@socketio.on("subscribe")
def on_subscribe(data):
    """
    Abonne le client aux metriques d'un serveur specifique.
    Utilise les rooms SocketIO pour filtrer les emissions.
    """
    server_id = data.get("server_id")
    if server_id:
        join_room(server_id)
        logger.debug(f"Client abonne aux metriques de '{server_id}'")


@socketio.on("unsubscribe")
def on_unsubscribe(data):
    """Desabonne le client des metriques d'un serveur."""
    server_id = data.get("server_id")
    if server_id:
        leave_room(server_id)
        logger.debug(f"Client desabonne des metriques de '{server_id}'")
