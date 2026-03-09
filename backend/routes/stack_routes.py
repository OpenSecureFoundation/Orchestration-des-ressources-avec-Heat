"""
Routes de gestion des stacks Heat
Deploiement, mise a jour, suppression
"""

from flask import Blueprint, request
from backend.services.stack_service import StackService
from backend.models.stack import Stack
from backend.utils.decorators import login_required
from backend.utils.helpers import success_response, error_response, log_action

stack_bp = Blueprint('stacks', __name__, url_prefix='/api/stacks')

@stack_bp.route('/', methods=['GET'])
@login_required
def list_stacks():
    """
    GET /api/stacks
    Lister toutes les stacks
    """
    user_id = request.current_user['id']
    role = request.current_user['role']

    # Admin voit toutes les stacks, user voit uniquement les siennes
    result = StackService.list_all_stacks(user_id=None if role == 'admin' else user_id)

    if not result['success']:
        return error_response(result['error'], 500)

    return success_response(result['stacks'])


@stack_bp.route('/<int:stack_db_id>', methods=['GET'])
@login_required
def get_stack(stack_db_id):
    """
    GET /api/stacks/:id
    Recuperer une stack specifique
    """
    stack = Stack.get_by_id(stack_db_id)

    if not stack:
        return error_response('Stack non trouvee', 404)

    # Verifier les permissions
    if stack['created_by'] != request.current_user['id'] and request.current_user['role'] != 'admin':
        return error_response('Acces refuse', 403)

    # Enrichir avec le statut OpenStack
    status_result = StackService.get_stack_status(stack['stack_id'])

    if status_result['success']:
        stack['current_status'] = status_result['status']
        stack['outputs'] = status_result['outputs']

    return success_response(stack)


@stack_bp.route('/', methods=['POST'])
@login_required
def create_stack():
    """
    POST /api/stacks
    Creer et deployer une nouvelle stack

    Body:
        {
            "name": "ma-stack",
            "template_id": 1,
            "parameters": {
                "key": "value"
            }
        }
    """
    data = request.get_json()

    if not data or 'name' not in data or 'template_id' not in data:
        return error_response('Champs name et template_id requis', 400)

    result = StackService.create_stack(
        name=data['name'],
        template_id=data['template_id'],
        parameters=data.get('parameters'),
        user_id=request.current_user['id']
    )

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='stack',
        level='INFO',
        message=f'Stack creee: {data["name"]}',
        details={'stack_id': result['stack_id']}
    )

    return success_response({
        'stack_id': result['stack_id'],
        'db_id': result['db_id']
    }, message='Stack en cours de creation')


@stack_bp.route('/<string:stack_id>/status', methods=['GET'])
@login_required
def get_stack_status(stack_id):
    """
    GET /api/stacks/:stack_id/status
    Recuperer le statut actuel d'une stack
    """
    result = StackService.get_stack_status(stack_id)

    if not result['success']:
        return error_response(result['error'], 404)

    return success_response({
        'status': result['status'],
        'outputs': result['outputs'],
        'resources': result['resources']
    })


@stack_bp.route('/<string:stack_id>/resources', methods=['GET'])
@login_required
def get_stack_resources(stack_id):
    """
    GET /api/stacks/:stack_id/resources
    Lister les ressources d'une stack
    """
    result = StackService.get_stack_resources(stack_id)

    if not result['success']:
        return error_response(result['error'], 404)

    return success_response(result['resources'])


@stack_bp.route('/<string:stack_id>', methods=['PUT'])
@login_required
def update_stack(stack_id):
    """
    PUT /api/stacks/:stack_id
    Mettre a jour une stack

    Body:
        {
            "template_id": 2,
            "parameters": {...}
        }
    """
    # Verifier les permissions
    stack = Stack.get_by_stack_id(stack_id)

    if not stack:
        return error_response('Stack non trouvee', 404)

    if stack['created_by'] != request.current_user['id'] and request.current_user['role'] != 'admin':
        return error_response('Acces refuse', 403)

    data = request.get_json()

    result = StackService.update_stack(
        stack_id=stack_id,
        template_id=data.get('template_id'),
        parameters=data.get('parameters')
    )

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='stack',
        level='INFO',
        message=f'Stack mise a jour: {stack["name"]}'
    )

    return success_response(message='Stack en cours de mise a jour')


@stack_bp.route('/<string:stack_id>', methods=['DELETE'])
@login_required
def delete_stack(stack_id):
    """
    DELETE /api/stacks/:stack_id
    Supprimer une stack
    """
    # Verifier les permissions
    stack = Stack.get_by_stack_id(stack_id)

    if not stack:
        return error_response('Stack non trouvee', 404)

    if stack['created_by'] != request.current_user['id'] and request.current_user['role'] != 'admin':
        return error_response('Acces refuse', 403)

    result = StackService.delete_stack(stack_id)

    if not result['success']:
        return error_response(result['error'], 500)

    log_action(
        user_id=request.current_user['id'],
        category='stack',
        level='INFO',
        message=f'Stack supprimee: {stack["name"]}'
    )

    return success_response(message='Stack en cours de suppression')


@stack_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """
    GET /api/stacks/statistics
    Recuperer les statistiques sur les stacks
    """
    user_id = None if request.current_user['role'] == 'admin' else request.current_user['id']

    stats = Stack.get_statistics(user_id=user_id)

    return success_response(stats)
