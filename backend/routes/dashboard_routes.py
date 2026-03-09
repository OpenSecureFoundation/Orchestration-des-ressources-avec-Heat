"""
Routes pour servir les pages HTML du dashboard
"""

from flask import Blueprint, render_template, session, redirect, url_for
from backend.services.auth_service import AuthService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """
    GET /
    Page d'accueil - redirection vers login ou dashboard
    """
    session_token = session.get('session_token')

    if session_token:
        user = AuthService.validate_session(session_token)
        if user:
            return redirect(url_for('dashboard.dashboard_page'))

    return redirect(url_for('dashboard.login_page'))


@dashboard_bp.route('/login')
def login_page():
    """
    GET /login
    Page de connexion
    """
    return render_template('login.html')


@dashboard_bp.route('/dashboard')
def dashboard_page():
    """
    GET /dashboard
    Dashboard principal (monitoring temps reel)
    """
    session_token = session.get('session_token')

    if not session_token:
        return redirect(url_for('dashboard.login_page'))

    user = AuthService.validate_session(session_token)

    if not user:
        return redirect(url_for('dashboard.login_page'))

    return render_template('dashboard.html', user=user)


@dashboard_bp.route('/templates')
def templates_page():
    """
    GET /templates
    Page de gestion des templates
    """
    session_token = session.get('session_token')

    if not session_token:
        return redirect(url_for('dashboard.login_page'))

    user = AuthService.validate_session(session_token)

    if not user:
        return redirect(url_for('dashboard.login_page'))

    return render_template('templates_manager.html', user=user)


@dashboard_bp.route('/stacks')
def stacks_page():
    """
    GET /stacks
    Page de gestion des stacks
    """
    session_token = session.get('session_token')

    if not session_token:
        return redirect(url_for('dashboard.login_page'))

    user = AuthService.validate_session(session_token)

    if not user:
        return redirect(url_for('dashboard.login_page'))

    return render_template('stacks_manager.html', user=user)


@dashboard_bp.route('/vms')
def vms_page():
    """
    GET /vms
    Page de gestion des VMs
    """
    session_token = session.get('session_token')

    if not session_token:
        return redirect(url_for('dashboard.login_page'))

    user = AuthService.validate_session(session_token)

    if not user:
        return redirect(url_for('dashboard.login_page'))

    return render_template('vms_manager.html', user=user)
