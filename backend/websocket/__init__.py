"""
Gestion WebSocket pour les mises a jour temps reel
"""

from .handlers import init_socketio, socketio

__all__ = ['init_socketio', 'socketio']
