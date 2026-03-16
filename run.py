"""
Point d'entree de l'application Heat Orchestration Platform.
Lance le serveur Flask avec SocketIO.
"""

import eventlet
eventlet.monkey_patch()

import sys
import os

# Ajout du repertoire racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app, socketio
from backend.config import Config

if __name__ == "__main__":
    app = create_app()

    ip_dashboard = Config.get_dashboard_ip()
    port = Config.DASHBOARD_PORT

    print("=" * 60)
    print("  Heat Orchestration Platform")
    print("=" * 60)
    print(f"  URL : http://{ip_dashboard}:{port}")
    print(f"  Environnement : {Config.FLASK_ENV}")
    print(f"  OpenStack : {Config.OS_AUTH_URL}")
    print(f"  Reseau public : {Config.PUBLIC_NETWORK_NAME}")
    print("=" * 60)
    print("  Ctrl+C pour arreter")
    print("=" * 60)

    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=Config.DEBUG,
    )
