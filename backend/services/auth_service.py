"""
Service d'authentification
Gere la connexion, deconnexion et les sessions utilisateurs
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from backend.models.user import User
from backend.config import Config
import secrets

class AuthService:
    """Service de gestion de l'authentification"""

    # Stockage des sessions en memoire
    # En production, utiliser Redis ou une base persistante
    _sessions = {}

    @staticmethod
    def login(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authentifier un utilisateur et creer une session

        Args:
            username: Nom d'utilisateur
            password: Mot de passe

        Returns:
            Dictionnaire avec user info et session_token, None si echec
        """
        user = User.authenticate(username, password)

        if not user:
            return None

        # Generer un token de session unique
        session_token = secrets.token_urlsafe(32)

        # Calculer l'expiration de la session
        expires_at = datetime.now() + timedelta(seconds=Config.SESSION_LIFETIME)

        # Stocker la session
        AuthService._sessions[session_token] = {
            'user': user,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }

        return {
            'user': user,
            'session_token': session_token,
            'expires_at': expires_at.isoformat()
        }

    @staticmethod
    def logout(session_token: str) -> bool:
        """
        Deconnecter un utilisateur

        Args:
            session_token: Token de session

        Returns:
            True si deconnexion reussie
        """
        if session_token in AuthService._sessions:
            del AuthService._sessions[session_token]
            return True
        return False

    @staticmethod
    def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
        """
        Valider une session et retourner l'utilisateur

        Args:
            session_token: Token de session

        Returns:
            Infos utilisateur si session valide, None sinon
        """
        if session_token not in AuthService._sessions:
            return None

        session = AuthService._sessions[session_token]

        # Verifier l'expiration
        if datetime.now() > session['expires_at']:
            # Session expiree, la supprimer
            del AuthService._sessions[session_token]
            return None

        return session['user']

    @staticmethod
    def extend_session(session_token: str) -> bool:
        """
        Prolonger la duree de vie d'une session

        Args:
            session_token: Token de session

        Returns:
            True si session prolongee
        """
        if session_token not in AuthService._sessions:
            return False

        # Prolonger l'expiration
        AuthService._sessions[session_token]['expires_at'] = \
            datetime.now() + timedelta(seconds=Config.SESSION_LIFETIME)

        return True

    @staticmethod
    def cleanup_expired_sessions():
        """Nettoyer les sessions expirees (a appeler periodiquement)"""
        now = datetime.now()
        expired = [
            token for token, session in AuthService._sessions.items()
            if now > session['expires_at']
        ]

        for token in expired:
            del AuthService._sessions[token]

        return len(expired)

    @staticmethod
    def get_active_sessions_count() -> int:
        """Obtenir le nombre de sessions actives"""
        AuthService.cleanup_expired_sessions()
        return len(AuthService._sessions)
