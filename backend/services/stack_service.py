"""
Service de gestion des stacks Heat
Gere le deploiement, la mise a jour et la suppression des stacks
Avec support des templates imbriques
"""

from typing import Optional, Dict, Any, List
from backend.models.stack import Stack
from backend.services.openstack_service import OpenStackService
from backend.models.template import Template
import time
import re
import yaml

class StackService:
    """Service de gestion des stacks Heat"""

    @staticmethod
    def create_stack(name: str, template_id: int, parameters: dict = None,
                    user_id: int = None) -> Dict[str, Any]:
        """
        Deploie une stack avec injection d'IP, gestion des templates imbriques
        et ouverture automatique des ports SSH (22) et Agent (8080).
        """
        template = Template.get_by_id(template_id)
        if not template:
            return {'success': False, 'stack_id': None, 'db_id': None, 'error': 'Template non trouve'}

        try:
            heat = OpenStackService.get_heat_client()
            neutron = OpenStackService.get_neutron_client()

            if parameters is None:
                parameters = {}

            # 1. Injection automatique de l'IP du Dashboard
            try:
                template_dict = yaml.safe_load(template['content'])
                if 'parameters' in template_dict and 'dashboard_ip' in template_dict['parameters']:
                    if 'dashboard_ip' not in parameters:
                        from backend.config import Config
                        parameters['dashboard_ip'] = Config.get_dashboard_ip()
                        print(f"[STACK] IP dashboard injectee: {parameters['dashboard_ip']}")
            except Exception as e:
                print(f"[STACK] Erreur injection IP: {e}")

            # 2. Ouverture des ports (Indispensable pour Linux Bridge)
            sec_group_id = parameters.get('security_group')
            if sec_group_id:
                for port in [22, 8080]:
                    try:
                        neutron.create_security_group_rule({
                            'security_group_rule': {
                                'direction': 'ingress',
                                'protocol': 'tcp',
                                'port_range_min': port,
                                'port_range_max': port,
                                'remote_ip_prefix': '0.0.0.0/0',
                                'security_group_id': sec_group_id
                            }
                        })
                        print(f"[STACK] Port {port} ouvert")
                    except Exception:
                        pass  # Deja existant

            # 3. Recuperation des templates imbriques (.yaml)
            files = {}
            referenced_templates = re.findall(r'type:\s+([a-zA-Z0-9_-]+\.yaml)', template['content'])

            print(f"[STACK] Templates imbriques detectes: {referenced_templates}")

            for ref_filename in referenced_templates:
                ref_name = ref_filename.replace('.yaml', '').replace('.yml', '')
                ref_template = Template.get_by_name(ref_name)
                if ref_template:
                    files[ref_filename] = ref_template['content']
                    print(f"[STACK] Template imbrique charge: {ref_filename}")

            # 4. Lancement de la creation
            create_args = {
                'stack_name': name,
                'template': template['content'],
                'parameters': parameters
            }

            if files:
                create_args['files'] = files
                print(f"[STACK] Creation avec {len(files)} fichier(s) imbrique(s)")

            stack = heat.stacks.create(**create_args)
            stack_id = stack['stack']['id']

            # 5. Enregistrement en base
            db_id = Stack.create(
                stack_id=stack_id,
                name=name,
                template_id=template_id,
                status='CREATE_IN_PROGRESS',
                parameters=parameters,
                created_by=user_id
            )

            print(f"[STACK] Stack creee: {name} (ID: {stack_id}, DB: {db_id})")

            return {
                'success': True,
                'stack_id': stack_id,
                'db_id': db_id,
                'error': None
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[STACK] ERREUR creation: {str(e)}")
            print(f"[STACK] Traceback:\n{error_detail}")

            return {
                'success': False,
                'stack_id': None,
                'db_id': None,
                'error': str(e)
            }

    @staticmethod
    def get_stack_status(stack_id: str) -> Dict[str, Any]:
        """
        Recuperer le statut d'une stack depuis OpenStack

        Returns:
            {'success': bool, 'status': str, 'outputs': dict, 'error': str}
        """
        try:
            heat = OpenStackService.get_heat_client()
            stack = heat.stacks.get(stack_id)

            # Extraire les outputs
            outputs = {}
            if hasattr(stack, 'outputs') and stack.outputs:
                for output in stack.outputs:
                    outputs[output['output_key']] = output['output_value']

            # Mettre a jour la base de donnees
            Stack.update_status(stack_id, stack.stack_status, outputs)

            return {
                'success': True,
                'status': stack.stack_status,
                'outputs': outputs,
                'resources': stack.to_dict() if hasattr(stack, 'to_dict') else {},
                'error': None
            }

        except Exception as e:
            print(f"[STACK] Erreur get_stack_status: {str(e)}")
            return {
                'success': False,
                'status': None,
                'outputs': None,
                'resources': None,
                'error': f'Erreur lors de la recuperation: {str(e)}'
            }

    @staticmethod
    def get_stack_resources(stack_id: str) -> Dict[str, Any]:
        """
        Recuperer la liste des ressources d'une stack

        Returns:
            {'success': bool, 'resources': list, 'error': str}
        """
        try:
            heat = OpenStackService.get_heat_client()
            resources = heat.resources.list(stack_id)

            resources_list = [
                {
                    'name': r.resource_name,
                    'type': r.resource_type,
                    'status': r.resource_status,
                    'id': r.physical_resource_id
                }
                for r in resources
            ]

            return {
                'success': True,
                'resources': resources_list,
                'error': None
            }

        except Exception as e:
            print(f"[STACK] Erreur get_stack_resources: {str(e)}")
            return {
                'success': False,
                'resources': None,
                'error': f'Erreur lors de la recuperation: {str(e)}'
            }

    @staticmethod
    def update_stack(stack_id: str, template_id: int = None,
                    parameters: dict = None) -> Dict[str, Any]:
        """
        Mettre a jour une stack existante avec support des templates imbriques

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            heat = OpenStackService.get_heat_client()

            update_args = {}

            if template_id:
                template = Template.get_by_id(template_id)
                if not template:
                    return {
                        'success': False,
                        'error': 'Template non trouve'
                    }

                update_args['template'] = template['content']

                # Gerer les templates imbriques pour la mise a jour aussi
                files = {}
                referenced_templates = re.findall(
                    r'type:\s+([a-zA-Z0-9_-]+\.yaml)',
                    template['content']
                )

                for ref_template_filename in referenced_templates:
                    ref_template_name = ref_template_filename.replace('.yaml', '').replace('.yml', '')
                    ref_template = Template.get_by_name(ref_template_name)

                    if ref_template:
                        files[ref_template_filename] = ref_template['content']

                if files:
                    update_args['files'] = files

            if parameters:
                update_args['parameters'] = parameters

            heat.stacks.update(stack_id, **update_args)

            # Mettre a jour le statut en base
            Stack.update_status(stack_id, 'UPDATE_IN_PROGRESS')

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            print(f"[STACK] Erreur update_stack: {str(e)}")
            return {
                'success': False,
                'error': f'Erreur lors de la mise a jour: {str(e)}'
            }

    @staticmethod
    def delete_stack(stack_id: str) -> Dict[str, Any]:
        """
        Supprimer une stack

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            heat = OpenStackService.get_heat_client()
            heat.stacks.delete(stack_id)

            # Marquer comme supprimee en base
            Stack.mark_deleted(stack_id)

            print(f"[STACK] Stack supprimee: {stack_id}")

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            print(f"[STACK] Erreur delete_stack: {str(e)}")
            return {
                'success': False,
                'error': f'Erreur lors de la suppression: {str(e)}'
            }

    @staticmethod
    def list_all_stacks(user_id: int = None) -> Dict[str, Any]:
        """
        Lister toutes les stacks actives (exclut les supprimees)

        Returns:
            {'success': bool, 'stacks': list, 'error': str}
        """
        try:
            # Recuperer depuis la base (TOUTES les stacks d'abord)
            all_db_stacks = Stack.get_all(user_id=user_id)

            # FILTRER : exclure les stacks supprimées
            db_stacks = [
                s for s in all_db_stacks
                if not (
                    s.get('status', '').startswith('DELETE') or
                    s.get('deleted', False) == True
                )
            ]

            print(f"[STACK] Stacks en base: {len(all_db_stacks)}, actives: {len(db_stacks)}")

            # Enrichir avec les infos OpenStack (avec gestion d'erreur)
            try:
                heat = OpenStackService.get_heat_client()

                for stack in db_stacks:
                    try:
                        os_stack = heat.stacks.get(stack['stack_id'])
                        stack['current_status'] = os_stack.stack_status

                        # Mettre a jour en base si different
                        if stack['current_status'] != stack['status']:
                            Stack.update_status(stack['stack_id'], stack['current_status'])

                        # Si la stack est supprimée dans OpenStack, la marquer en base
                        if stack['current_status'].startswith('DELETE'):
                            Stack.mark_deleted(stack['stack_id'])

                    except Exception as stack_error:
                        # Stack supprimée dans OpenStack mais encore en base
                        print(f"[STACK] Stack {stack['stack_id']} non trouvee dans Heat: {stack_error}")
                        stack['current_status'] = stack.get('status', 'UNKNOWN')

                        # Si erreur 404, marquer comme supprimée
                        if '404' in str(stack_error) or 'not found' in str(stack_error).lower():
                            Stack.mark_deleted(stack['stack_id'])

            except Exception as heat_error:
                # Heat inaccessible, utiliser juste les données de la base
                print(f"[STACK] Heat inaccessible: {heat_error}")
                for stack in db_stacks:
                    stack['current_status'] = stack.get('status', 'UNKNOWN')

            # Filtrer à nouveau après enrichissement (au cas où)
            active_stacks = [
                s for s in db_stacks
                if not s.get('current_status', '').startswith('DELETE')
            ]

            print(f"[STACK] Stacks retournees: {len(active_stacks)}")

            return {
                'success': True,
                'stacks': active_stacks,
                'error': None
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[STACK] Erreur list_all_stacks: {str(e)}")
            print(f"[STACK] Traceback:\n{error_detail}")

            return {
                'success': False,
                'stacks': [],
                'error': f'Erreur lors de la recuperation: {str(e)}'
            }

    @staticmethod
    def wait_for_stack_complete(stack_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        Attendre qu'une stack atteigne un etat final

        Args:
            stack_id: ID de la stack
            timeout: Timeout en secondes

        Returns:
            {'success': bool, 'status': str, 'error': str}
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = StackService.get_stack_status(stack_id)

            if not result['success']:
                return result

            status = result['status']

            # Etats finaux
            if 'COMPLETE' in status or 'FAILED' in status:
                return {
                    'success': 'COMPLETE' in status,
                    'status': status,
                    'error': None if 'COMPLETE' in status else 'Stack creation failed'
                }

            # Attendre 5 secondes avant de reessayer
            time.sleep(5)

        return {
            'success': False,
            'status': None,
            'error': 'Timeout atteint'
        }
