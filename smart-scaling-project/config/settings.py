# import os

# # ─── CONFIGURATION KEYSTONE ──────────────────────────────────────────────────
# # Ces paramètres permettent de générer les tokens de session sécurisés
# AUTH_CONFIG = {
#     "auth_url": os.environ.get("OS_AUTH_URL", "http://localhost:5000/v3"),
#     "username": os.environ.get("OS_USERNAME", "admin"),
#     "password": os.environ.get("OS_PASSWORD", "admin"),  # <── Ton pass ici
#     "project_name": os.environ.get("OS_PROJECT_NAME", "admin"),
#     "user_domain_name": "Default",
#     "project_domain_name": "Default",
#     "region_name": "RegionOne",
# }

# # ─── CATALOGUE DES FLAVORS (Scaling Vertical) ───────────────────────────────
# # Ordre logique pour le resize automatique
# FLAVOR_SEQUENCE = ["m1.tiny", "m1.small", "m1.medium", "m1.large", "m1.xlarge"]

# # ─── POLITIQUES DE SCALING ──────────────────────────────────────────────────
# SCALING_POLICY = {target_flavor_name
#     "cpu_upper_threshold": 80.0,   # Seuil pour Scale-Up
#     "cpu_lower_threshold": 25.0,   # Seuil pour Scale-Down
#     "ram_upper_threshold": 85.0,
#     "cooldown_seconds": 300,       # Protection anti-yoyo (5 min)
#     "monitor_interval": 60,        # Fréquence de check Gnocchi
# }

# # ─── CHEMINS DES LOGS ───────────────────────────────────────────────────────
# LOG_DIR = "logs"
# AUDIT_LOG = os.path.join(LOG_DIR, "audit_scaling.log")


import os
from datetime import timedelta

class Config:
    """
    Configuration centralisée pour le projet Heat Orchestration & Scaling.
    Aligne le code sur les seuils définis dans le Cahier d'Analyse.
    """
    
    # --- Authentification Keystone (SSI) ---
    AUTH_URL = os.environ.get("OS_AUTH_URL", "http://localhost:5000/v3")
    USERNAME = os.environ.get("OS_USERNAME", "admin")
    PASSWORD = os.environ.get("OS_PASSWORD", "admin")
    PROJECT_NAME = os.environ.get("OS_PROJECT_NAME", "admin")
    USER_DOMAIN_NAME = "Default"
    PROJECT_DOMAIN_NAME = "Default"

    # --- Paramètres de Scaling Intelligent (Cahier de Conception) ---
    # Liste ordonnée des flavors pour le scaling vertical
    FLAVOR_SEQUENCE = ["m1.tiny", "m1.small", "m1.medium", "m1.large", "m1.xlarge"]
    
    # Seuils de décision (Use Case : Surveillance Métrique)
    CPU_HIGH_THRESHOLD = 80.0  # % - Déclenche Scale-UP
    CPU_LOW_THRESHOLD = 20.0   # % - Déclenche Scale-DOWN
    
    # Mécanisme Anti-Oscillation (Cooldown)
    # Temps d'attente minimal entre deux opérations de scaling
    SCALING_COOLDOWN = 300  # 5 minutes
    
    # Intervalle de monitoring Gnocchi
    MONITOR_INTERVAL = 60  # secondes

    # --- Logs & Audit ---
    LOG_FILE = "logs/scaling_audit.log"
    PORT = 8765