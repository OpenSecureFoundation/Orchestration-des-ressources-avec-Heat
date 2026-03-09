"""
Decorateurs pour les routes Flask
"""

from functools import wraps
from flask import request, jsonify, session
from backend.services.auth_service import AuthService

def login_required(f):
    """
    Decorateur pour proteger les routes necessitant une authentification

    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifier le token de session
        session_token = request.headers.get('X-Session-Token') or session.get('session_token')

        if not session_token:
            return jsonify({
                'success': False,
                'error': 'Non authentifie'
            }), 401

        # Valider la session
        user = AuthService.validate_session(session_token)

        if not user:
            return jsonify({
                'success': False,
                'error': 'Session invalide ou expiree'
            }), 401

        # Prolonger la session
        AuthService.extend_session(session_token)

        # Ajouter l'utilisateur au contexte de la requete
        request.current_user = user

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorateur pour proteger les routes necessitant un role admin

    Usage:
        @app.route('/admin')
        @login_required
        @admin_required
        def admin_route():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifier que l'utilisateur est authentifie (doit etre utilise apres @login_required)
        if not hasattr(request, 'current_user'):
            return jsonify({
                'success': False,
                'error': 'Non authentifie'
            }), 401

        # Verifier le role
        if request.current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'error': 'Acces refuse - role admin requis'
            }), 403

        return f(*args, **kwargs)

    return decorated_function
