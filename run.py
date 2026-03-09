#!/usr/bin/env python3
"""
Point d'entree principal de l'application
Lance le serveur Flask avec SocketIO
"""

from backend.app import create_app
from backend.config import Config

if __name__ == '__main__':
    # Creer l'application
    app = create_app()

    # Importer socketio apres la creation de l'app
    from backend.websocket.handlers import socketio

    print(f"""
    ========================================
    Orchestration Heat - Dashboard
    ========================================
    URL: http://{Config.HOST}:{Config.PORT}
    Debug: {Config.DEBUG}
    ========================================
    """)

    # Lancer le serveur avec SocketIO
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False  # Desactive car incompatible avec threading
    )
