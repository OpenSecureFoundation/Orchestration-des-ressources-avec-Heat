"""
Service de gestion des templates Heat
Gere l'import, la creation, la modification et la validation des templates
"""

import os
import yaml
from typing import Optional, Dict, Any, List
from backend.models.template import Template
from backend.config import Config

class TemplateService:
    """Service de gestion des templates Heat"""

    @staticmethod
    def validate_yaml(content: str) -> Dict[str, Any]:
        """
        Valider la syntaxe YAML d'un template

        Args:
            content: Contenu YAML du template

        Returns:
            {'valid': bool, 'error': str or None, 'parsed': dict or None}
        """
        try:
            parsed = yaml.safe_load(content)

            # Verifier les champs obligatoires pour un template Heat
            if not isinstance(parsed, dict):
                return {
                    'valid': False,
                    'error': 'Le template doit etre un dictionnaire YAML',
                    'parsed': None
                }

            if 'heat_template_version' not in parsed:
                return {
                    'valid': False,
                    'error': 'Champ heat_template_version manquant',
                    'parsed': None
                }

            if 'resources' not in parsed:
                return {
                    'valid': False,
                    'error': 'Section resources manquante',
                    'parsed': None
                }

            return {
                'valid': True,
                'error': None,
                'parsed': parsed
            }

        except yaml.YAMLError as e:
            return {
                'valid': False,
                'error': f'Erreur de syntaxe YAML: {str(e)}',
                'parsed': None
            }

    @staticmethod
    def create_template(name: str, content: str, description: str = None,
                       template_type: str = 'created', source_url: str = None,
                       user_id: int = None, is_public: bool = False) -> Dict[str, Any]:
        """
        Creer un nouveau template

        Returns:
            {'success': bool, 'template_id': int, 'error': str}
        """
        # Valider le YAML
        validation = TemplateService.validate_yaml(content)
        if not validation['valid']:
            return {
                'success': False,
                'template_id': None,
                'error': validation['error']
            }

        # Verifier que le nom n'existe pas deja
        existing = Template.get_by_name(name)
        if existing:
            return {
                'success': False,
                'template_id': None,
                'error': f'Un template nomme "{name}" existe deja'
            }

        try:
            template_id = Template.create(
                name=name,
                content=content,
                description=description,
                template_type=template_type,
                source_url=source_url,
                created_by=user_id,
                is_public=is_public
            )

            return {
                'success': True,
                'template_id': template_id,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'template_id': None,
                'error': f'Erreur lors de la creation: {str(e)}'
            }

    @staticmethod
    def load_builtin_templates() -> int:
        """
        Charger les templates builtin depuis le dossier templates_storage/builtin

        Returns:
            Nombre de templates charges
        """
        builtin_path = Config.BUILTIN_TEMPLATES_PATH

        if not os.path.exists(builtin_path):
            return 0

        loaded = 0

        for filename in os.listdir(builtin_path):
            if not filename.endswith('.yaml'):
                continue

            filepath = os.path.join(builtin_path, filename)

            with open(filepath, 'r') as f:
                content = f.read()

            name = filename.replace('.yaml', '')

            # Verifier si le template existe deja
            if Template.get_by_name(name):
                continue

            # Creer le template
            result = TemplateService.create_template(
                name=name,
                content=content,
                description=f'Template builtin: {name}',
                template_type='builtin',
                is_public=True
            )

            if result['success']:
                loaded += 1

        return loaded

    @staticmethod
    def get_template_parameters(template_id: int) -> Dict[str, Any]:
        """
        Extraire les parametres d'un template

        Returns:
            {'success': bool, 'parameters': dict, 'error': str}
        """
        template = Template.get_by_id(template_id)

        if not template:
            return {
                'success': False,
                'parameters': None,
                'error': 'Template non trouve'
            }

        validation = TemplateService.validate_yaml(template['content'])

        if not validation['valid']:
            return {
                'success': False,
                'parameters': None,
                'error': validation['error']
            }

        parsed = validation['parsed']
        parameters = parsed.get('parameters', {})

        return {
            'success': True,
            'parameters': parameters,
            'error': None
        }

    @staticmethod
    def save_uploaded_template(filename: str, content: str, user_id: int) -> Dict[str, Any]:
        """
        Sauvegarder un template uploade

        Returns:
            {'success': bool, 'template_id': int, 'error': str}
        """
        # Nettoyer le nom de fichier
        name = filename.replace('.yaml', '').replace('.yml', '')

        # Ajouter un suffixe unique si le nom existe
        base_name = name
        counter = 1
        while Template.get_by_name(name):
            name = f"{base_name}_{counter}"
            counter += 1

        return TemplateService.create_template(
            name=name,
            content=content,
            description=f'Template uploade: {filename}',
            template_type='uploaded',
            user_id=user_id,
            is_public=False
        )
