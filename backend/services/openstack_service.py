"""
Client OpenStack unifie.
Gere l'authentification et fournit des clients pour chaque service.
"""

import logging
from keystoneauth1.identity import v3
from keystoneauth1 import session as ks_session
from heatclient import client as heat_client
from novaclient import client as nova_client
from neutronclient.v2_0 import client as neutron_client
from keystoneclient.v3 import client as keystone_client

from backend.config import Config

logger = logging.getLogger(__name__)


class OpenStackService:
    """Fournit des clients authentifies pour les services OpenStack."""

    @staticmethod
    def _get_session():
        """
        Cree une session Keystone authentifiee.
        Utilise les credentials du fichier .env.
        """
        creds = Config.get_openstack_credentials()
        auth = v3.Password(
            auth_url=creds["auth_url"],
            username=creds["username"],
            password=creds["password"],
            project_name=creds["project_name"],
            user_domain_name=creds["user_domain_name"],
            project_domain_name=creds["project_domain_name"],
        )
        return ks_session.Session(auth=auth)

    @staticmethod
    def get_heat_client():
        """Retourne un client Heat authentifie."""
        try:
            sess = OpenStackService._get_session()
            endpoint = f"{Config.OS_AUTH_URL.replace(':5000/v3', ':8004')}/v1"
            # Recuperation du project_id depuis la session
            project_id = sess.get_project_id()
            heat_endpoint = f"http://controller:8004/v1/{project_id}"
            return heat_client.Client(
                "1",
                endpoint=heat_endpoint,
                session=sess
            )
        except Exception as e:
            logger.error(f"Erreur creation client Heat : {e}")
            raise

    @staticmethod
    def get_nova_client():
        """Retourne un client Nova authentifie."""
        try:
            sess = OpenStackService._get_session()
            return nova_client.Client("2.1", session=sess)
        except Exception as e:
            logger.error(f"Erreur creation client Nova : {e}")
            raise

    @staticmethod
    def get_neutron_client():
        """Retourne un client Neutron authentifie."""
        try:
            sess = OpenStackService._get_session()
            return neutron_client.Client(session=sess)
        except Exception as e:
            logger.error(f"Erreur creation client Neutron : {e}")
            raise

    @staticmethod
    def get_keystone_client():
        """Retourne un client Keystone authentifie."""
        try:
            sess = OpenStackService._get_session()
            return keystone_client.Client(session=sess)
        except Exception as e:
            logger.error(f"Erreur creation client Keystone : {e}")
            raise

    @staticmethod
    def verify_connection() -> bool:
        """
        Verifie que la connexion OpenStack fonctionne.
        Tente d'authentifier et de lister les projets.
        """
        try:
            sess = OpenStackService._get_session()
            sess.get_token()
            logger.info("Connexion OpenStack verifiee avec succes")
            return True
        except Exception as e:
            logger.error(f"Echec connexion OpenStack : {e}")
            return False

    @staticmethod
    def get_public_network_id() -> str:
        """
        Retourne l'ID du reseau public.
        Utilise le nom configure ou detecte automatiquement le reseau externe.
        """
        try:
            nc = OpenStackService.get_neutron_client()
            # Recherche par nom configure
            reseaux = nc.list_networks(name=Config.PUBLIC_NETWORK_NAME)
            if reseaux["networks"]:
                network_id = reseaux["networks"][0]["id"]
                logger.debug(f"Reseau public trouve : {network_id}")
                return network_id

            # Fallback : chercher n'importe quel reseau externe
            reseaux_externes = nc.list_networks(**{"router:external": True})
            if reseaux_externes["networks"]:
                network_id = reseaux_externes["networks"][0]["id"]
                logger.warning(
                    f"Reseau '{Config.PUBLIC_NETWORK_NAME}' introuvable, "
                    f"utilisation de : {network_id}"
                )
                return network_id

            raise ValueError("Aucun reseau public/externe trouve")
        except Exception as e:
            logger.error(f"Erreur recuperation reseau public : {e}")
            raise

    @staticmethod
    def get_available_images() -> list:
        """Liste les images Glance disponibles."""
        try:
            nc = OpenStackService.get_nova_client()
            images = nc.glance.list()
            return [
                {"id": img.id, "name": img.name, "status": img.status}
                for img in images
            ]
        except Exception as e:
            logger.error(f"Erreur liste images : {e}")
            return []

    @staticmethod
    def get_available_flavors() -> list:
        """Liste les flavors Nova disponibles."""
        try:
            nc = OpenStackService.get_nova_client()
            flavors = nc.flavors.list()
            return [
                {
                    "id": f.id,
                    "name": f.name,
                    "ram": f.ram,
                    "vcpus": f.vcpus,
                    "disk": f.disk,
                }
                for f in flavors
            ]
        except Exception as e:
            logger.error(f"Erreur liste flavors : {e}")
            return []

    @staticmethod
    def get_keypairs() -> list:
        """Liste les paires de cles Nova disponibles."""
        try:
            nc = OpenStackService.get_nova_client()
            keypairs = nc.keypairs.list()
            return [{"name": kp.name} for kp in keypairs]
        except Exception as e:
            logger.error(f"Erreur liste keypairs : {e}")
            return []
