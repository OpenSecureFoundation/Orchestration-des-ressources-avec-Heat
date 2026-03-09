"""
Routes d'authentification
Gere le login, logout et la gestion des sessions
"""

from flask import Blueprint, request, jsonify, session
from backend.services.auth_service import AuthService
from backend.models.user import User
from backend.utils.helpers import success_response, error_response, log_action
from backend.utils.decorators import login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Authentifier un utilisateur

    Body:
        {
            "username": "admin",
            "password": "password"
        }

    Returns:
        {
            "success": true,
            "user": {...},
            "session_token": "..."
        }
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return error_response('Username et password requis', 400)

    username = data['username']
    password = data['password']

    # Authentifier
    result = AuthService.login(username, password)

    if not result:
        log_action(
            category='auth',
            level='WARNING',
            message=f'Tentative de connexion echouee pour {username}'
        )
        return error_response('Identifiants invalides', 401)

    # Stocker le token en session Flask
    session['session_token'] = result['session_token']
    session['user_id'] = result['user']['id']

    log_action(
        user_id=result['user']['id'],
        category='auth',
        level='INFO',
        message=f'Connexion reussie pour {username}'
    )

    return success_response({
        'user': result['user'],
        'session_token': result['session_token']
    })


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    POST /api/auth/logout
    Deconnecter l'utilisateur actuel
    """
    session_token = session.get('session_token')

    if session_token:
        AuthService.logout(session_token)

    # Nettoyer la session Flask
    session.clear()

    log_action(
        user_id=request.current_user['id'],
        category='auth',
        level='INFO',
        message='Deconnexion'
    )

    return success_response(message='Deconnexion reussie')


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    GET /api/auth/me
    Obtenir les informations de l'utilisateur connecte
    """
    return success_response(request.current_user)


@auth_bp.route('/validate', methods=['GET'])
def validate_session():
    """
    GET /api/auth/validate
    Valider une session
    """
    session_token = request.headers.get('X-Session-Token') or session.get('session_token')

    if not session_token:
        return error_response('Aucune session', 401)

    user = AuthService.validate_session(session_token)

    if not user:
        return error_response('Session invalide', 401)

    return success_response({
        'valid': True,
        'user': user
    })
