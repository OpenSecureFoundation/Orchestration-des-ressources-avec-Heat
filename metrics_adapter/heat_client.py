"""
heat_client.py
Responsabilité : Communication avec OpenStack (Heat + Nova).
C'est ce fichier qui envoie concrètement les commandes
de resize à OpenStack quand un scaling est décidé.
"""

import os
import logging
import time
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURATION DU LOGGER
# ============================================================
logger = logging.getLogger("heat_client")

# ============================================================
# IDENTIFIANTS OPENSTACK (depuis .env)
# ============================================================
OS_CONFIG = {
    "auth_url":     os.getenv("OS_AUTH_URL",      "http://localhost:5000/v3"),
    "username":     os.getenv("OS_USERNAME",      "admin"),
    "password":     os.getenv("OS_PASSWORD",      "admin"),
    "project_name": os.getenv("OS_PROJECT_NAME",  "admin"),
    "user_domain":  os.getenv("OS_USER_DOMAIN",   "Default"),
    "proj_domain":  os.getenv("OS_PROJ_DOMAIN",   "Default"),
}

# Cooldown : délai minimum entre deux scalings (en secondes)
# Evite les oscillations (scale up puis scale down en boucle)
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "120"))

# ============================================================
# ÉTAT INTERNE DU CLIENT
# Garde en mémoire le dernier scaling effectué
# ============================================================
_state = {
    "last_scaling_time": 0,       # timestamp du dernier scaling
    "current_flavor":    "m1.small",
    "vm_id":             None,
    "stack_name":        os.getenv("STACK_NAME", "heat-main-stack"),
    "connected":         False,   # True si connecté à OpenStack
}

# Clients OpenStack (initialisés lors de la connexion)
_nova_client = None
_heat_client = None


# ============================================================
# CONNEXION À OPENSTACK
# ============================================================
def connecter() -> bool:
    """
    Se connecte à OpenStack via Keystone.
    Initialise les clients Nova (VMs) et Heat (orchestration).

    Retourne :
        True  → connexion réussie
        False → échec (OpenStack indisponible)
    """
    global _nova_client, _heat_client, _state

    try:
        # Import des bibliothèques OpenStack
        from keystoneauth1 import loading, session
        from heatclient import client as heat_client_lib
        from novaclient import client as nova_client_lib

        # Chargement des identifiants Keystone
        loader = loading.get_plugin_loader("password")
        auth = loader.load_from_options(
            auth_url=OS_CONFIG["auth_url"],
            username=OS_CONFIG["username"],
            password=OS_CONFIG["password"],
            project_name=OS_CONFIG["project_name"],
            user_domain_name=OS_CONFIG["user_domain"],
            project_domain_name=OS_CONFIG["proj_domain"],
        )

        sess = session.Session(auth=auth)

        # Initialisation client Heat
        _heat_client = heat_client_lib.Client("1", session=sess)

        # Initialisation client Nova
        _nova_client = nova_client_lib.Client("2.1", session=sess)

        _state["connected"] = True
        logger.info("Connexion à OpenStack réussie")
        return True

    except ImportError:
        # OpenStack non installé → mode simulation
        logger.warning(
            "Bibliothèques OpenStack non disponibles. "
            "Passage en mode simulation."
        )
        _state["connected"] = False
        return False

    except Exception as e:
        logger.error(f"Erreur de connexion à OpenStack : {e}")
        _state["connected"] = False
        return False


# ============================================================
# RÉCUPÉRER L'ID DE LA VM
# ============================================================
def recuperer_vm_id(vm_name: str) -> str | None:
    """
    Récupère l'ID OpenStack d'une VM par son nom.

    Paramètres :
        vm_name (str) : Nom de la VM dans OpenStack

    Retourne :
        L'ID de la VM ou None si introuvable
    """
    if not _state["connected"] or _nova_client is None:
        logger.warning("Non connecté à OpenStack - ID VM simulé")
        return "mock-vm-id-12345"

    try:
        serveurs = _nova_client.servers.list(
            search_opts={"name": vm_name}
        )
        if serveurs:
            vm_id = serveurs[0].id
            _state["vm_id"] = vm_id
            logger.info(f"VM trouvée : {vm_name} → ID: {vm_id}")
            return vm_id
        else:
            logger.error(f"VM introuvable : {vm_name}")
            return None

    except Exception as e:
        logger.error(f"Erreur récupération VM ID : {e}")
        return None


# ============================================================
# VÉRIFIER LE COOLDOWN
# ============================================================
def cooldown_respecte() -> bool:
    """
    Vérifie qu'on attend bien le délai minimum entre deux scalings.
    Evite les oscillations rapides de flavor.

    Retourne :
        True  → on peut scaler
        False → trop tôt, on attend encore
    """
    temps_ecoule = time.time() - _state["last_scaling_time"]

    if temps_ecoule < COOLDOWN_SECONDS:
        attente = COOLDOWN_SECONDS - temps_ecoule
        logger.info(
            f"Cooldown actif : encore {attente:.0f}s avant "
            f"le prochain scaling autorisé"
        )
        return False

    return True


# ============================================================
# FONCTION PRINCIPALE : EFFECTUER LE RESIZE
# ============================================================
def effectuer_resize(vm_name: str, nouveau_flavor: str) -> dict:
    """
    Effectue le resize vertical d'une VM vers un nouveau flavor.
    C'est l'action finale du pipeline de scaling.

    Paramètres :
        vm_name       (str) : Nom de la VM à resizer
        nouveau_flavor (str) : Flavor cible (ex: "m1.medium")

    Retourne un dict avec :
        success (bool)   : True si le resize a réussi
        message (str)    : Description du résultat
        ancien_flavor    : Flavor avant le resize
        nouveau_flavor   : Flavor après le resize
    """
    ancien_flavor = _state["current_flavor"]

    # --- Pas de changement nécessaire ---
    if nouveau_flavor == ancien_flavor:
        msg = f"Déjà sur le flavor {ancien_flavor} — aucun resize nécessaire"
        logger.info(msg)
        return {
            "success": True,
            "message": msg,
            "ancien_flavor": ancien_flavor,
            "nouveau_flavor": nouveau_flavor,
            "action": "none"
        }

    # --- Vérification du cooldown ---
    if not cooldown_respecte():
        msg = f"Cooldown actif — resize reporté ({ancien_flavor} → {nouveau_flavor})"
        logger.warning(msg)
        return {
            "success": False,
            "message": msg,
            "ancien_flavor": ancien_flavor,
            "nouveau_flavor": nouveau_flavor,
            "action": "cooldown"
        }

    # --- Mode simulation (OpenStack non disponible) ---
    if not _state["connected"] or _nova_client is None:
        return _simuler_resize(vm_name, ancien_flavor, nouveau_flavor)

    # --- Resize réel via OpenStack Nova ---
    return _resize_openstack(vm_name, ancien_flavor, nouveau_flavor)


def _resize_openstack(
        vm_name: str,
        ancien_flavor: str,
        nouveau_flavor: str) -> dict:
    """
    Effectue le resize via l'API OpenStack Nova.
    Appelé uniquement quand OpenStack est disponible.
    """
    try:
        # Récupérer l'ID de la VM si pas encore fait
        if _state["vm_id"] is None:
            _state["vm_id"] = recuperer_vm_id(vm_name)

        if _state["vm_id"] is None:
            return {
                "success": False,
                "message": f"VM introuvable : {vm_name}",
                "ancien_flavor": ancien_flavor,
                "nouveau_flavor": nouveau_flavor,
                "action": "error"
            }

        # Récupérer l'objet flavor cible
        flavors = _nova_client.flavors.list()
        flavor_obj = next(
            (f for f in flavors if f.name == nouveau_flavor),
            None
        )

        if flavor_obj is None:
            return {
                "success": False,
                "message": f"Flavor introuvable : {nouveau_flavor}",
                "ancien_flavor": ancien_flavor,
                "nouveau_flavor": nouveau_flavor,
                "action": "error"
            }

        # Lancer le resize
        serveur = _nova_client.servers.get(_state["vm_id"])
        serveur.resize(flavor_obj)

        logger.info(
            f"Resize lancé : {vm_name} "
            f"{ancien_flavor} → {nouveau_flavor}"
        )

        # Attendre que le resize soit en état VERIFY_RESIZE
        _attendre_statut(serveur, "VERIFY_RESIZE", timeout=120)

        # Confirmer le resize
        serveur.confirm_resize()

        # Mise à jour de l'état interne
        _state["current_flavor"] = nouveau_flavor
        _state["last_scaling_time"] = time.time()

        msg = (
            f"Resize réussi : {vm_name} "
            f"{ancien_flavor} → {nouveau_flavor}"
        )
        logger.info(msg)

        return {
            "success": True,
            "message": msg,
            "ancien_flavor": ancien_flavor,
            "nouveau_flavor": nouveau_flavor,
            "action": "resized"
        }

    except Exception as e:
        msg = f"Erreur lors du resize : {e}"
        logger.error(msg)
        return {
            "success": False,
            "message": msg,
            "ancien_flavor": ancien_flavor,
            "nouveau_flavor": nouveau_flavor,
            "action": "error"
        }


def _attendre_statut(
        serveur,
        statut_cible: str,
        timeout: int = 120) -> bool:
    """
    Attend qu'une VM atteigne un statut donné.
    Vérifie toutes les 5 secondes jusqu'au timeout.
    """
    debut = time.time()

    while time.time() - debut < timeout:
        serveur.get()   # Rafraîchit les données du serveur
        statut = serveur.status

        logger.info(f"Statut VM : {statut} (attente : {statut_cible})")

        if statut == statut_cible:
            return True

        if statut == "ERROR":
            logger.error("VM en erreur pendant le resize")
            return False

        time.sleep(5)

    logger.error(f"Timeout atteint en attendant le statut {statut_cible}")
    return False


def _simuler_resize(
        vm_name: str,
        ancien_flavor: str,
        nouveau_flavor: str) -> dict:
    """
    Simule un resize quand OpenStack n'est pas disponible.
    Utilisé pour les tests et le développement.
    """
    logger.info(
        f"[SIMULATION] Resize : {vm_name} "
        f"{ancien_flavor} → {nouveau_flavor}"
    )

    # Simule un délai de traitement
    time.sleep(1)

    # Mise à jour de l'état interne
    _state["current_flavor"] = nouveau_flavor
    _state["last_scaling_time"] = time.time()

    msg = (
        f"[SIMULATION] Resize réussi : {vm_name} "
        f"{ancien_flavor} → {nouveau_flavor}"
    )
    logger.info(msg)

    return {
        "success": True,
        "message": msg,
        "ancien_flavor": ancien_flavor,
        "nouveau_flavor": nouveau_flavor,
        "action": "simulated"
    }


# ============================================================
# FONCTIONS D'INFORMATION
# ============================================================
def get_statut_stack() -> dict:
    """
    Récupère le statut de la stack Heat principale.
    Retourne des données simulées si OpenStack est indisponible.
    """
    if not _state["connected"] or _heat_client is None:
        return {
            "name":    _state["stack_name"],
            "status":  "SIMULATED",
            "flavor":  _state["current_flavor"],
            "message": "OpenStack non disponible - mode simulation"
        }

    try:
        stack = _heat_client.stacks.get(_state["stack_name"])
        return {
            "name":   stack.stack_name,
            "status": stack.stack_status,
            "flavor": _state["current_flavor"],
        }
    except Exception as e:
        logger.error(f"Erreur récupération statut stack : {e}")
        return {
            "name":    _state["stack_name"],
            "status":  "ERROR",
            "flavor":  _state["current_flavor"],
            "message": str(e)
        }


def get_flavor_actuel() -> str:
    """Retourne le flavor actuellement utilisé par la VM."""
    return _state["current_flavor"]


def get_etat_connexion() -> bool:
    """Retourne True si connecté à OpenStack."""
    return _state["connected"]