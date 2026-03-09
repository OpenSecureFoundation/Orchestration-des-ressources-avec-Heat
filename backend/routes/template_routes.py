"""
Routes de gestion des templates Heat
CRUD complet + import Git + upload
"""

from flask import Blueprint, request, jsonify
from backend.services.template_service import TemplateService
from backend.services.git_service import GitService
from backend.models.template import Template
from backend.utils.decorators import login_required
from backend.utils.helpers import success_response, error_response, log_action

template_bp = Blueprint('templates', __name__, url_prefix='/api/templates')

@template_bp.route('/', methods=['GET'])
@login_required
def list_templates():
    """
    GET /api/templates
    Lister tous les templates accessibles

    Query params:
        ?type=builtin|git|uploaded|created
    """
    template_type = request.args.get('type')
    user_id = request.current_user['id']

    templates = Template.get_all(user_id=user_id, include_public=True)

    # Filtrer par type si specifie
    if template_type:
        templates = [t for t in templates if t['type'] == template_type]

    return success_response(templates)


@template_bp.route('/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """
    GET /api/templates/:id
    Recuperer un template specifique
    """
    template = Template.get_by_id(template_id)

    if not template:
        return error_response('Template non trouve', 404)

    # Verifier les permissions
    user_id = request.current_user['id']
    if not template['is_public'] and template['created_by'] != user_id:
        return error_response('Acces refuse', 403)

    return success_response(template)


@template_bp.route('/', methods=['POST'])
@login_required
def create_template():
    """
    POST /api/templates
    Creer un nouveau template

    Body:
        {
            "name": "mon-template",
            "content": "heat_template_version: ...",
            "description": "Description",
            "is_public": false
        }
    """
    data = request.get_json()

    if not data or 'name' not in data or 'content' not in data:
        return error_response('Champs name et content requis', 400)

    result = TemplateService.create_template(
        name=data['name'],
        content=data['content'],
        description=data.get('description'),
        template_type='created',
        user_id=request.current_user['id'],
        is_public=data.get('is_public', False)
    )

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='template',
        level='INFO',
        message=f'Template cree: {data["name"]}'
    )

    return success_response({
        'template_id': result['template_id']
    }, message='Template cree avec succes')


@template_bp.route('/<int:template_id>', methods=['PUT'])
@login_required
def update_template(template_id):
    """
    PUT /api/templates/:id
    Mettre a jour un template

    Body:
        {
            "content": "nouveau contenu",
            "description": "nouvelle description",
            "is_public": true
        }
    """
    template = Template.get_by_id(template_id)

    if not template:
        return error_response('Template non trouve', 404)

    # Verifier les permissions
    if template['created_by'] != request.current_user['id']:
        return error_response('Acces refuse', 403)

    data = request.get_json()

    # Valider le nouveau contenu si fourni
    if 'content' in data:
        validation = TemplateService.validate_yaml(data['content'])
        if not validation['valid']:
            return error_response(validation['error'], 400)

    success = Template.update(
        template_id=template_id,
        content=data.get('content'),
        description=data.get('description'),
        is_public=data.get('is_public')
    )

    if not success:
        return error_response('Aucune modification effectuee', 400)

    log_action(
        user_id=request.current_user['id'],
        category='template',
        level='INFO',
        message=f'Template modifie: {template["name"]}'
    )

    return success_response(message='Template mis a jour')


@template_bp.route('/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    """
    DELETE /api/templates/:id
    Supprimer un template
    """
    template = Template.get_by_id(template_id)

    if not template:
        return error_response('Template non trouve', 404)

    # Verifier les permissions
    if template['created_by'] != request.current_user['id']:
        return error_response('Acces refuse', 403)

    # Interdire la suppression des templates builtin
    if template['type'] == 'builtin':
        return error_response('Impossible de supprimer un template builtin', 403)

    success = Template.delete(template_id)

    if not success:
        return error_response('Erreur lors de la suppression', 500)

    log_action(
        user_id=request.current_user['id'],
        category='template',
        level='INFO',
        message=f'Template supprime: {template["name"]}'
    )

    return success_response(message='Template supprime')


@template_bp.route('/import-git', methods=['POST'])
@login_required
def import_from_git():
    """
    POST /api/templates/import-git
    Importer des templates depuis un depot Git

    Body:
        {
            "repo_url": "https://github.com/user/repo",
            "branch": "main"
        }
    """
    data = request.get_json()

    if not data or 'repo_url' not in data:
        return error_response('repo_url requis', 400)

    repo_url = data['repo_url']
    branch = data.get('branch', 'main')

    # Valider l'URL
    if not GitService.validate_git_url(repo_url):
        return error_response('URL Git invalide', 400)

    result = GitService.clone_and_import_templates(
        repo_url=repo_url,
        branch=branch,
        user_id=request.current_user['id']
    )

    if not result['success']:
        return error_response(
            'Echec de l import',
            400,
            details={'errors': result['errors']}
        )

    log_action(
        user_id=request.current_user['id'],
        category='template',
        level='INFO',
        message=f'Import Git: {len(result["templates"])} templates',
        details={'repo': repo_url, 'branch': branch}
    )

    return success_response(
        data={
            'imported': result['templates'],
            'errors': result['errors']
        },
        message=f'{len(result["templates"])} templates importes'
    )


@template_bp.route('/upload', methods=['POST'])
@login_required
def upload_template():
    """
    POST /api/templates/upload
    Uploader un fichier template

    Form data:
        file: fichier YAML
    """
    if 'file' not in request.files:
        return error_response('Aucun fichier fourni', 400)

    file = request.files['file']

    if file.filename == '':
        return error_response('Nom de fichier vide', 400)

    if not (file.filename.endswith('.yaml') or file.filename.endswith('.yml')):
        return error_response('Le fichier doit etre au format YAML', 400)

    # Lire le contenu
    content = file.read().decode('utf-8')

    result = TemplateService.save_uploaded_template(
        filename=file.filename,
        content=content,
        user_id=request.current_user['id']
    )

    if not result['success']:
        return error_response(result['error'], 400)

    log_action(
        user_id=request.current_user['id'],
        category='template',
        level='INFO',
        message=f'Template uploade: {file.filename}'
    )

    return success_response({
        'template_id': result['template_id']
    }, message='Template uploade avec succes')


@template_bp.route('/<int:template_id>/parameters', methods=['GET'])
@login_required
def get_template_parameters(template_id):
    """
    GET /api/templates/:id/parameters
    Extraire les parametres d'un template
    """
    result = TemplateService.get_template_parameters(template_id)

    if not result['success']:
        return error_response(result['error'], 404)

    return success_response(result['parameters'])
