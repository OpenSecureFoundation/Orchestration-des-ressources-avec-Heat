"""
Routes de gestion des VMs (serveurs Nova)
Operations sur les instances virtuelles
"""

from flask import Blueprint, request
from backend.services.vm_service import VMService
from backend.utils.decorators import login_required
from backend.utils.helpers import success_response, error_response, log_action

vm_bp = Blueprint('vms', __name__, url_prefix='/api/vms')

@vm_bp.route('/', methods=['GET'])
@login_required
def list_servers():
    """
    GET /api/vms
    Lister tous les serveurs
    """
    result = VMService.list_servers()

    if not result['success']:
        return error_response(result['error'], 500)

    return success_response(result['servers'])


@vm_bp.route('/<string:server_id>', methods=['GET'])
@login_required
def get_server(server_id):
    """
    GET /api/vms/:server_id
    Recuperer les details d'un serveur
    """
    result = VMService.get_server(server_id)

    if not result['success']:
        return error_response(result['error'], 404)

    return success_response(result['server'])


@vm_bp.route('/<string:server_id>/start', methods=['POST'])
@login_required
def start_server(server_id):
    """
    POST /api/vms/:server_id/start
    Demarrer un serveur arrete
    """
    result = VMService.start_server(server_id)

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='vm',
        level='INFO',
        message=f'Serveur demarre: {server_id}'
    )

    return success_response(message='Serveur en cours de demarrage')


@vm_bp.route('/<string:server_id>/stop', methods=['POST'])
@login_required
def stop_server(server_id):
    """
    POST /api/vms/:server_id/stop
    Arreter un serveur
    """
    result = VMService.stop_server(server_id)

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='vm',
        level='INFO',
        message=f'Serveur arrete: {server_id}'
    )

    return success_response(message='Serveur en cours d arret')


@vm_bp.route('/<string:server_id>/reboot', methods=['POST'])
@login_required
def reboot_server(server_id):
    """
    POST /api/vms/:server_id/reboot
    Redemarrer un serveur

    Body (optionnel):
        {
            "hard": false
        }
    """
    data = request.get_json() or {}
    hard = data.get('hard', False)

    result = VMService.reboot_server(server_id, hard=hard)

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='vm',
        level='INFO',
        message=f'Serveur redemarré ({"hard" if hard else "soft"}): {server_id}'
    )

    return success_response(message='Serveur en cours de redemarrage')


@vm_bp.route('/<string:server_id>/resize', methods=['POST'])
@login_required
def resize_server(server_id):
    """
    POST /api/vms/:server_id/resize
    Redimensionner un serveur (changer de flavor)

    Body:
        {
            "flavor": "m1.medium"
        }
    """
    data = request.get_json()

    if not data or 'flavor' not in data:
        return error_response('Champ flavor requis', 400)

    result = VMService.resize_server(server_id, data['flavor'])

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='vm',
        level='INFO',
        message=f'Resize demande: {server_id} -> {data["flavor"]}'
    )

    return success_response(message='Resize en cours')


@vm_bp.route('/<string:server_id>/confirm-resize', methods=['POST'])
@login_required
def confirm_resize(server_id):
    """
    POST /api/vms/:server_id/confirm-resize
    Confirmer un resize
    """
    result = VMService.confirm_resize(server_id)

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='vm',
        level='INFO',
        message=f'Resize confirme: {server_id}'
    )

    return success_response(message='Resize confirme')


@vm_bp.route('/<string:server_id>', methods=['DELETE'])
@login_required
def delete_server(server_id):
    """
    DELETE /api/vms/:server_id
    Supprimer un serveur
    """
    result = VMService.delete_server(server_id)

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='vm',
        level='WARNING',
        message=f'Serveur supprime: {server_id}'
    )

    return success_response(message='Serveur en cours de suppression')
