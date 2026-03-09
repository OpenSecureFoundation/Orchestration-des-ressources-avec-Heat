"""
Service de gestion des VMs (serveurs Nova)
Gere les operations sur les instances virtuelles
"""

from typing import Optional, Dict, Any, List
from backend.services.openstack_service import OpenStackService

class VMService:
    """Service de gestion des VMs"""

    @staticmethod
    def list_servers(user_id: int = None) -> Dict[str, Any]:
        """
        Lister tous les serveurs

        Returns:
            {'success': bool, 'servers': list, 'error': str}
        """
        try:
            nova = OpenStackService.get_nova_client()
            servers = nova.servers.list()

            servers_list = []
            for server in servers:
                # Recuperer les addresses IP
                addresses = []
                for network_name, network_addresses in server.addresses.items():
                    for addr in network_addresses:
                        addresses.append({
                            'network': network_name,
                            'type': addr.get('OS-EXT-IPS:type', 'unknown'),
                            'address': addr['addr']
                        })

                # Recuperer le flavor
                flavor = nova.flavors.get(server.flavor['id'])

                servers_list.append({
                    'id': server.id,
                    'name': server.name,
                    'status': server.status,
                    'flavor': {
                        'id': flavor.id,
                        'name': flavor.name,
                        'vcpus': flavor.vcpus,
                        'ram': flavor.ram,
                        'disk': flavor.disk
                    },
                    'addresses': addresses,
                    'created': server.created,
                    'updated': server.updated
                })

            return {
                'success': True,
                'servers': servers_list,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'servers': None,
                'error': f'Erreur lors de la recuperation: {str(e)}'
            }

    @staticmethod
    def get_server(server_id: str) -> Dict[str, Any]:
        """
        Recuperer les details d'un serveur

        Returns:
            {'success': bool, 'server': dict, 'error': str}
        """
        try:
            nova = OpenStackService.get_nova_client()
            server = nova.servers.get(server_id)

            # Recuperer le flavor
            flavor = nova.flavors.get(server.flavor['id'])

            # Addresses IP
            addresses = []
            for network_name, network_addresses in server.addresses.items():
                for addr in network_addresses:
                    addresses.append({
                        'network': network_name,
                        'type': addr.get('OS-EXT-IPS:type', 'unknown'),
                        'address': addr['addr']
                    })

            server_info = {
                'id': server.id,
                'name': server.name,
                'status': server.status,
                'flavor': {
                    'id': flavor.id,
                    'name': flavor.name,
                    'vcpus': flavor.vcpus,
                    'ram': flavor.ram,
                    'disk': flavor.disk
                },
                'addresses': addresses,
                'created': server.created,
                'updated': server.updated,
                'metadata': server.metadata
            }

            return {
                'success': True,
                'server': server_info,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'server': None,
                'error': f'Erreur lors de la recuperation: {str(e)}'
            }

    @staticmethod
    def start_server(server_id: str) -> Dict[str, Any]:
        """
        Demarrer un serveur arrete

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            nova = OpenStackService.get_nova_client()
            server = nova.servers.get(server_id)
            server.start()

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors du demarrage: {str(e)}'
            }

    @staticmethod
    def stop_server(server_id: str) -> Dict[str, Any]:
        """
        Arreter un serveur

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            nova = OpenStackService.get_nova_client()
            server = nova.servers.get(server_id)
            server.stop()

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de l arret: {str(e)}'
            }

    @staticmethod
    def reboot_server(server_id: str, hard: bool = False) -> Dict[str, Any]:
        """
        Redemarrer un serveur

        Args:
            server_id: ID du serveur
            hard: True pour reboot force (hard), False pour reboot gracieux (soft)
        """
        try:
            nova = OpenStackService.get_nova_client()
            server = nova.servers.get(server_id)

            reboot_type = 'HARD' if hard else 'SOFT'
            server.reboot(reboot_type=reboot_type)

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors du redemarrage: {str(e)}'
            }

    @staticmethod
    def resize_server(server_id: str, new_flavor_name: str) -> Dict[str, Any]:
        """
        Redimensionner un serveur (changer de flavor)

        Args:
            new_flavor_name: NOM du flavor (pas l'ID)

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            nova = OpenStackService.get_nova_client()
            server = nova.servers.get(server_id)

            print(f"[RESIZE] Serveur trouvé: {server.name}")
            print(f"[RESIZE] Flavor actuel: {server.flavor}")
            print(f"[RESIZE] Flavor demandé: {new_flavor_name}")

            # Lister TOUS les flavors disponibles
            all_flavors = nova.flavors.list()
            print(f"[RESIZE] Flavors disponibles:")
            for f in all_flavors:
                print(f"  - ID: {f.id}, Name: {f.name}")

            # Chercher le flavor par nom
            target_flavor = None
            for flavor in all_flavors:
                if flavor.name == new_flavor_name:
                    target_flavor = flavor
                    break

            if not target_flavor:
                available_names = [f.name for f in all_flavors]
                return {
                    'success': False,
                    'error': f'Flavor "{new_flavor_name}" non trouvé. Disponibles: {", ".join(available_names)}'
                }

            print(f"[RESIZE] Flavor trouvé: ID={target_flavor.id}, Name={target_flavor.name}")

            # Lancer le resize avec l'ID
            print(f"[RESIZE] Lancement resize vers flavor ID: {target_flavor.id}")
            server.resize(target_flavor.id)

            print(f"[RESIZE] Resize lancé avec succès")

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[RESIZE] ERREUR: {str(e)}")
            print(f"[RESIZE] Traceback:\n{error_detail}")

            return {
                'success': False,
                'error': f'Erreur lors du resize: {str(e)}'
            }

    @staticmethod
    def confirm_resize(server_id: str) -> Dict[str, Any]:
        """
        Confirmer un resize (apres verification)

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            nova = OpenStackService.get_nova_client()
            server = nova.servers.get(server_id)
            server.confirm_resize()

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de la confirmation: {str(e)}'
            }

    @staticmethod
    def delete_server(server_id: str) -> Dict[str, Any]:
        """
        Supprimer un serveur

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            nova = OpenStackService.get_nova_client()
            server = nova.servers.get(server_id)
            server.delete()

            return {
                'success': True,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de la suppression: {str(e)}'
            }
