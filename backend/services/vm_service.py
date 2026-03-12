"""
Service de gestion des machines virtuelles via Nova.
"""

import logging
import time
import threading

from backend.services.openstack_service import OpenStackService
from backend.models.metric import Metric

logger = logging.getLogger(__name__)

_resize_en_cours = {}
_flavors_cache = {}

def _get_flavor_nom(nc, flavor_id):
    if flavor_id in _flavors_cache:
        return _flavors_cache[flavor_id]
    try:
        for f in nc.flavors.list():
            _flavors_cache[str(f.id)] = f.name
        return _flavors_cache.get(str(flavor_id), flavor_id)
    except Exception:
        return flavor_id


def _thread_resize(vm_id: str, flavor_id: str):
    """
    Thread de fond qui attend VERIFY_RESIZE puis confirme.
    Permet de ne pas bloquer la requete HTTP Flask.
    """
    _resize_en_cours[vm_id] = "en_cours"
    try:
        nc = OpenStackService.get_nova_client()
        delai_max = 300
        debut = time.time()
        while time.time() - debut < delai_max:
            server = nc.servers.get(vm_id)
            if server.status == "VERIFY_RESIZE":
                server.confirm_resize()
                logger.info(f"[Thread] Resize confirme pour VM '{vm_id}' -> flavor '{flavor_id}'")
                _resize_en_cours[vm_id] = "termine"
                return
            if server.status == "ERROR":
                logger.error(f"[Thread] VM '{vm_id}' en erreur pendant resize")
                _resize_en_cours[vm_id] = "erreur"
                return
            if server.status == "ACTIVE" and server.flavor.get("original_name") == flavor_id:
                logger.info(f"[Thread] VM '{vm_id}' deja ACTIVE avec le bon flavor")
                _resize_en_cours[vm_id] = "termine"
                return
            logger.debug(f"[Thread] VM '{vm_id}' statut={server.status}, attente...")
            time.sleep(10)
        logger.warning(f"[Thread] Timeout resize VM '{vm_id}' apres {delai_max}s")
        _resize_en_cours[vm_id] = "timeout"
    except Exception as e:
        logger.error(f"[Thread] Erreur resize VM '{vm_id}' : {e}")
        _resize_en_cours[vm_id] = "erreur"


class VMService:
    """Gestion des operations sur les VMs Nova."""

    @staticmethod
    def list_all_vms() -> list:
        """
        Liste toutes les VMs disponibles dans le projet Nova.
        Inclut les IPs, flavor et statut.
        """
        try:
            nc = OpenStackService.get_nova_client()
            servers = nc.servers.list(detailed=True)
            resultats = []

            for server in servers:
                # Extraction des adresses IP
                ips = []
                for reseau, adresses in server.addresses.items():
                    for addr in adresses:
                        ips.append(addr["addr"])

                # Recuperation du nom du flavor — résolution ID -> nom si nécessaire
                flavor_info = server.flavor
                flavor_name = flavor_info.get("original_name") or flavor_info.get("id", "inconnu")
                if flavor_name and str(flavor_name).isdigit():
                    flavor_name = _get_flavor_nom(nc, flavor_name)

                resultats.append({
                    "id": server.id,
                    "name": server.name,
                    "status": server.status,
                    "flavor": flavor_name,
                    "flavor_id": flavor_info.get("id"),
                    "ip_addresses": ips,
                    "ip": ips[0] if ips else None,
                    "created": server.created,
                    "updated": server.updated,
                })

            return resultats

        except Exception as e:
            logger.error(f"Erreur liste VMs : {e}")
            raise

    @staticmethod
    def get_vm_details(vm_id: str) -> dict:
        """Retourne les details complets d'une VM avec flavor et image resolus."""
        try:
            nc = OpenStackService.get_nova_client()
            server = nc.servers.get(vm_id)

            ips = []
            for reseau, adresses in server.addresses.items():
                for addr in adresses:
                    ips.append({"network": reseau, "ip": addr["addr"],
                                "type": addr.get("OS-EXT-IPS:type", "fixed")})

            # Resolution flavor ID -> nom + details
            flavor_id = server.flavor.get("id", "")
            flavor_nom = server.flavor.get("original_name", "")
            vcpus = ram = disk = None
            try:
                f = nc.flavors.get(flavor_id)
                flavor_nom = f.name
                vcpus = f.vcpus
                ram   = f.ram
                disk  = f.disk
            except Exception:
                if not flavor_nom and flavor_id:
                    flavor_nom = _get_flavor_nom(nc, flavor_id)

            flavor_enrichi = {
                "id": flavor_id,
                "original_name": flavor_nom or flavor_id,
                "vcpus": vcpus,
                "ram": ram,
                "disk": disk,
            }

            # Resolution image ID -> nom via Nova
            image_nom = ""
            try:
                image_id = (server.image or {}).get("id", "")
                if image_id:
                    img = nc.glance.find_image(image_id)
                    image_nom = img.name if img else image_id
            except Exception:
                pass

            return {
                "id": server.id,
                "name": server.name,
                "status": server.status,
                "flavor": flavor_enrichi,
                "image_name": image_nom,
                "ip_addresses": ips,
                "created": server.created,
                "updated": server.updated,
                "key_name": server.key_name,
                "security_groups": [sg["name"] for sg in (server.security_groups or [])],
                "metadata": server.metadata,
            }

        except Exception as e:
            logger.error(f"Erreur details VM '{vm_id}' : {e}")
            raise

    @staticmethod
    def resize_vm(vm_id: str, new_flavor: str) -> bool:
        """
        Redimensionne une VM vers un nouveau flavor.
        Lance le resize puis surveille en thread de fond.
        Retourne immediatement sans bloquer la requete HTTP.
        """
        try:
            nc = OpenStackService.get_nova_client()
            server = nc.servers.get(vm_id)

            # Resolution nom -> ID numerique (Nova exige l'ID)
            flavor_id = new_flavor
            try:
                flavors = nc.flavors.list()
                for f in flavors:
                    if f.name == new_flavor or str(f.id) == str(new_flavor):
                        flavor_id = str(f.id)
                        logger.debug(f"Flavor '{new_flavor}' resolu en ID '{flavor_id}'")
                        break
            except Exception:
                pass

            # Si la VM est deja en VERIFY_RESIZE, juste confirmer
            if server.status == "VERIFY_RESIZE":
                logger.info(f"VM '{server.name}' deja en VERIFY_RESIZE, confirmation directe")
                server.confirm_resize()
                logger.info(f"Resize confirme pour VM '{vm_id}'")
                return True

            logger.info(f"Resize VM '{server.name}' : '{new_flavor}' (ID={flavor_id})")
            server.resize(flavor_id)

            # Lancer le thread de confirmation en arriere-plan
            t = threading.Thread(
                target=_thread_resize,
                args=(vm_id, new_flavor),
                daemon=True
            )
            t.start()
            logger.info(f"Thread resize lance pour VM '{vm_id}'")
            return True

        except Exception as e:
            logger.error(f"Erreur resize VM '{vm_id}' : {e}")
            raise

    @staticmethod
    def get_resize_status(vm_id: str) -> str:
        """Retourne le statut du resize en cours pour une VM."""
        return _resize_en_cours.get(vm_id, "inconnu")

    @staticmethod
    def get_console_log(vm_id: str) -> str:
        """Recupere les derniers logs console d'une VM."""
        try:
            nc = OpenStackService.get_nova_client()
            server = nc.servers.get(vm_id)
            log = server.get_console_output(length=100)
            return log
        except Exception as e:
            logger.error(f"Erreur log console VM '{vm_id}' : {e}")
            return f"Impossible de recuperer les logs : {e}"

    @staticmethod
    def get_vm_metrics(vm_id: str) -> dict:
        """
        Recupere les dernieres metriques connues d'une VM depuis la base.
        """
        try:
            metrique = (
                Metric.query
                .filter_by(server_id=vm_id)
                .order_by(Metric.timestamp.desc())
                .first()
            )
            if metrique:
                return metrique.to_dict()
            return {}
        except Exception as e:
            logger.error(f"Erreur metriques VM '{vm_id}' : {e}")
            return {}

    @staticmethod
    def get_available_flavors() -> list:
        """Liste les flavors disponibles pour le resize."""
        return OpenStackService.get_available_flavors()
