"""
validator.py
Responsabilité : Sécurité et validation des alertes reçues des VMs.
Avant toute action de scaling, chaque alerte passe par ce module.
"""

import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURATION DU LOGGER
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("validator")

# ============================================================
# TOKEN SECRET
# Partagé entre les VMs et l'adaptateur.
# Défini dans le fichier .env
# ============================================================
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "heat-secret-token")

# ============================================================
# RÈGLES DE VALIDATION
# ============================================================
RULES = {
    "cpu_min": 0,
    "cpu_max": 100,
    "ram_min": 0,
    "ram_max": 100,
    # Une alerte ne doit pas avoir plus de 60 secondes
    "max_age_seconds": 60,
    # Champs obligatoires dans chaque alerte
    "required_fields": ["source", "token", "cpu", "ram", "timestamp"]
}


# ============================================================
# FONCTION PRINCIPALE DE VALIDATION
# ============================================================
def valider_alerte(data: dict) -> tuple[bool, str]:
    """
    Valide une alerte reçue d'une VM.

    Paramètres :
        data (dict) : Le contenu JSON de l'alerte reçue.

    Retourne :
        (True, "OK")           → alerte valide, on peut agir
        (False, "raison")      → alerte rejetée, raison du rejet
    """

    # --- ÉTAPE 1 : Vérifier que data n'est pas vide ---
    if not data:
        logger.warning("Alerte rejetée : données vides")
        return False, "Données vides"

    # --- ÉTAPE 2 : Vérifier les champs obligatoires ---
    for champ in RULES["required_fields"]:
        if champ not in data:
            logger.warning(f"Alerte rejetée : champ manquant '{champ}'")
            return False, f"Champ obligatoire manquant : {champ}"

    # --- ÉTAPE 3 : Vérifier le token secret ---
    if data["token"] != SECRET_TOKEN:
        logger.warning(
            f"Alerte rejetée : token invalide depuis '{data.get('source', 'inconnu')}'"
        )
        return False, "Token d'authentification invalide"

    # --- ÉTAPE 4 : Vérifier que les valeurs CPU sont valides ---
    cpu = data["cpu"]
    if not isinstance(cpu, (int, float)):
        logger.warning(f"Alerte rejetée : CPU n'est pas un nombre ({cpu})")
        return False, "La valeur CPU doit être un nombre"

    if not (RULES["cpu_min"] <= cpu <= RULES["cpu_max"]):
        logger.warning(f"Alerte rejetée : CPU hors limites ({cpu}%)")
        return False, f"CPU hors limites : {cpu}% (attendu entre 0 et 100)"

    # --- ÉTAPE 5 : Vérifier que les valeurs RAM sont valides ---
    ram = data["ram"]
    if not isinstance(ram, (int, float)):
        logger.warning(f"Alerte rejetée : RAM n'est pas un nombre ({ram})")
        return False, "La valeur RAM doit être un nombre"

    if not (RULES["ram_min"] <= ram <= RULES["ram_max"]):
        logger.warning(f"Alerte rejetée : RAM hors limites ({ram}%)")
        return False, f"RAM hors limites : {ram}% (attendu entre 0 et 100)"

    # --- ÉTAPE 6 : Vérifier que l'alerte n'est pas trop vieille ---
    timestamp = data["timestamp"]
    age = time.time() - timestamp

    if age > RULES["max_age_seconds"]:
        logger.warning(
            f"Alerte rejetée : trop ancienne ({age:.0f}s) "
            f"depuis '{data['source']}'"
        )
        return False, f"Alerte trop ancienne : {age:.0f} secondes"

    if age < 0:
        logger.warning("Alerte rejetée : timestamp dans le futur")
        return False, "Timestamp invalide : date dans le futur"

    # --- ÉTAPE 7 : Vérifier que la source est identifiée ---
    source = data["source"]
    if not isinstance(source, str) or len(source.strip()) == 0:
        logger.warning("Alerte rejetée : source non identifiée")
        return False, "Source non identifiée"

    # Tout est valide
    logger.info(
        f"Alerte validée depuis '{source}' — "
        f"CPU: {cpu}% | RAM: {ram}%"
    )
    return True, "OK"


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================
def determiner_action(cpu: float, policies: dict) -> str:
    """
    Détermine l'action de scaling à effectuer selon le CPU
    et les politiques configurées.

    Retourne :
        "scale_up"   → CPU dépasse le seuil haut
        "scale_down" → CPU est sous le seuil bas
        "none"       → Aucune action nécessaire
    """
    scale_up_threshold   = policies.get("scale_up_threshold", 80)
    scale_down_threshold = policies.get("scale_down_threshold", 20)

    if cpu > scale_up_threshold:
        logger.info(
            f"Action décidée : SCALE UP "
            f"(CPU {cpu}% > seuil {scale_up_threshold}%)"
        )
        return "scale_up"

    if cpu < scale_down_threshold:
        logger.info(
            f"Action décidée : SCALE DOWN "
            f"(CPU {cpu}% < seuil {scale_down_threshold}%)"
        )
        return "scale_down"

    logger.info(
        f"Action décidée : AUCUNE "
        f"(CPU {cpu}% dans la zone normale)"
    )
    return "none"


def determiner_nouveau_flavor(action: str, flavor_actuel: str) -> str:
    """
    Détermine le nouveau flavor à appliquer selon
    l'action et le flavor actuel de la VM.

    Retourne le nom du nouveau flavor.
    Si déjà au max ou au min, retourne le flavor actuel.
    """

    # Table de progression des flavors
    progression = {
        "scale_up": {
            "m1.small":  "m1.medium",   # small  → medium
            "m1.medium": "m1.large",    # medium → large
            "m1.large":  "m1.large",    # déjà au max
        },
        "scale_down": {
            "m1.large":  "m1.medium",   # large  → medium
            "m1.medium": "m1.small",    # medium → small
            "m1.small":  "m1.small",    # déjà au min
        }
    }

    if action not in progression:
        return flavor_actuel

    nouveau_flavor = progression[action].get(flavor_actuel, flavor_actuel)

    if nouveau_flavor == flavor_actuel:
        if action == "scale_up":
            logger.info(f"Déjà au flavor maximum : {flavor_actuel}")
        else:
            logger.info(f"Déjà au flavor minimum : {flavor_actuel}")
    else:
        logger.info(
            f"Changement de flavor : {flavor_actuel} → {nouveau_flavor}"
        )

    return nouveau_flavor