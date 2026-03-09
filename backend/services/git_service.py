"""
Service de gestion Git
Gere le clone et l'import de templates depuis des depots Git
"""

import os
import tempfile
import shutil
from typing import Dict, Any, List
from git import Repo, GitCommandError
from backend.services.template_service import TemplateService

class GitService:
    """Service de gestion des imports Git"""

    @staticmethod
    def clone_and_import_templates(repo_url: str, branch: str = 'main',
                                   user_id: int = None) -> Dict[str, Any]:
        """
        Cloner un depot Git et importer tous les templates YAML

        Args:
            repo_url: URL du depot Git
            branch: Branche a cloner
            user_id: ID de l'utilisateur

        Returns:
            {'success': bool, 'templates': list, 'errors': list}
        """
        temp_dir = None
        imported_templates = []
        errors = []

        try:
            # Creer un repertoire temporaire
            temp_dir = tempfile.mkdtemp()

            # Cloner le depot
            try:
                repo = Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
            except GitCommandError as e:
                return {
                    'success': False,
                    'templates': [],
                    'errors': [f'Erreur lors du clone Git: {str(e)}']
                }

            # Chercher tous les fichiers YAML
            yaml_files = []
            for root, dirs, files in os.walk(temp_dir):
                # Ignorer le dossier .git
                if '.git' in root:
                    continue

                for file in files:
                    if file.endswith('.yaml') or file.endswith('.yml'):
                        yaml_files.append(os.path.join(root, file))

            if not yaml_files:
                return {
                    'success': False,
                    'templates': [],
                    'errors': ['Aucun fichier YAML trouve dans le depot']
                }

            # Importer chaque template
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, 'r') as f:
                        content = f.read()

                    # Generer un nom a partir du chemin du fichier
                    relative_path = os.path.relpath(yaml_file, temp_dir)
                    name = relative_path.replace('.yaml', '').replace('.yml', '').replace('/', '_')

                    # Importer le template
                    result = TemplateService.create_template(
                        name=name,
                        content=content,
                        description=f'Importe depuis Git: {repo_url}',
                        template_type='git',
                        source_url=repo_url,
                        user_id=user_id,
                        is_public=False
                    )

                    if result['success']:
                        imported_templates.append({
                            'name': name,
                            'template_id': result['template_id'],
                            'file': relative_path
                        })
                    else:
                        errors.append(f'{relative_path}: {result["error"]}')

                except Exception as e:
                    errors.append(f'{yaml_file}: {str(e)}')

            return {
                'success': len(imported_templates) > 0,
                'templates': imported_templates,
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'templates': [],
                'errors': [f'Erreur generale: {str(e)}']
            }

        finally:
            # Nettoyer le repertoire temporaire
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    @staticmethod
    def validate_git_url(url: str) -> bool:
        """
        Valider une URL Git

        Args:
            url: URL a valider

        Returns:
            True si l'URL semble valide
        """
        valid_prefixes = [
            'https://github.com/',
            'https://gitlab.com/',
            'https://bitbucket.org/',
            'git@github.com:',
            'git@gitlab.com:'
        ]

        return any(url.startswith(prefix) for prefix in valid_prefixes)
