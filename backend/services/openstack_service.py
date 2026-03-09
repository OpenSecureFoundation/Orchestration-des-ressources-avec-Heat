"""
Service OpenStack
Gere la communication avec les APIs OpenStack (Heat, Nova, Neutron, etc.)
"""

from typing import Optional, Dict, Any, List
import os
from keystoneauth1 import session
from keystoneauth1.identity import v3
from heatclient import client as heat_client
from novaclient import client as nova_client
from neutronclient.v2_0 import client as neutron_client
from backend.config import Config

class OpenStackService:
    """Service de communication avec OpenStack"""

    _session = None
    _heat = None
    _nova = None
    _neutron = None

    @classmethod
    def _get_session(cls):
        """Obtenir une session Keystone (singleton)"""
        if cls._session is None:
            auth = v3.Password(
                auth_url=Config.OS_AUTH_URL,
                username=Config.OS_USERNAME,
                password=Config.OS_PASSWORD,
                project_name=Config.OS_PROJECT_NAME,
                user_domain_name=Config.OS_USER_DOMAIN_NAME,
                project_domain_name=Config.OS_PROJECT_DOMAIN_NAME
            )
            cls._session = session.Session(auth=auth)

        return cls._session

    @classmethod
    def get_heat_client(cls):
        """Obtenir le client Heat"""
        if cls._heat is None:
            sess = cls._get_session()
            cls._heat = heat_client.Client('1', session=sess)
        return cls._heat

    @classmethod
    def get_nova_client(cls):
        """Obtenir le client Nova"""
        if cls._nova is None:
            sess = cls._get_session()
            cls._nova = nova_client.Client('2', session=sess)
        return cls._nova

    @classmethod
    def get_neutron_client(cls):
        """Obtenir le client Neutron"""
        if cls._neutron is None:
            sess = cls._get_session()
            cls._neutron = neutron_client.Client(session=sess)
        return cls._neutron

    @classmethod
    def test_connection(cls) -> Dict[str, Any]:
        """
        Tester la connexion OpenStack

        Returns:
            Dictionnaire avec le statut de chaque service
        """
        results = {
            'heat': False,
            'nova': False,
            'neutron': False,
            'error': None
        }

        try:
            # Tester Heat
            heat = cls.get_heat_client()
            heat.build_info.build_info()
            results['heat'] = True
        except Exception as e:
            results['error'] = f"Heat: {str(e)}"

        try:
            # Tester Nova
            nova = cls.get_nova_client()
            nova.flavors.list()
            results['nova'] = True
        except Exception as e:
            if not results['error']:
                results['error'] = f"Nova: {str(e)}"

        try:
            # Tester Neutron
            neutron = cls.get_neutron_client()
            neutron.list_networks()
            results['neutron'] = True
        except Exception as e:
            if not results['error']:
                results['error'] = f"Neutron: {str(e)}"

        return results

    @classmethod
    def get_flavors(cls) -> List[Dict[str, Any]]:
        """Recuperer la liste des flavors disponibles"""
        nova = cls.get_nova_client()
        flavors = nova.flavors.list()

        return [
            {
                'id': f.id,
                'name': f.name,
                'vcpus': f.vcpus,
                'ram': f.ram,
                'disk': f.disk
            }
            for f in flavors
        ]

    @classmethod
    def get_images(cls) -> List[Dict[str, Any]]:
        """Recuperer la liste des images disponibles"""
        nova = cls.get_nova_client()
        images = nova.glance.list()

        return [
            {
                'id': img.id,
                'name': img.name,
                'status': img.status
            }
            for img in images
        ]

    @classmethod
    def get_networks(cls) -> List[Dict[str, Any]]:
        """Recuperer la liste des reseaux"""
        neutron = cls.get_neutron_client()
        networks = neutron.list_networks()['networks']

        return [
            {
                'id': net['id'],
                'name': net['name'],
                'subnets': net.get('subnets', []),
                'external': net.get('router:external', False)
            }
            for net in networks
        ]

    @classmethod
    def get_keypairs(cls) -> List[Dict[str, Any]]:
        """Recuperer la liste des keypairs SSH"""
        nova = cls.get_nova_client()
        keypairs = nova.keypairs.list()

        return [
            {
                'name': kp.name,
                'fingerprint': kp.fingerprint
            }
            for kp in keypairs
        ]
