"""
Configuration de l'application
Charge les variables depuis le fichier .env
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration globale de l'application"""

    # Configuration Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('FLASK_PORT', 8080))
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')

    # Base de donnees
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/orchestration.db')

    # Chemins des templates
    BUILTIN_TEMPLATES_PATH = os.getenv('BUILTIN_TEMPLATES_PATH', 'templates_storage/builtin')
    USER_TEMPLATES_PATH = os.getenv('USER_TEMPLATES_PATH', 'templates_storage/user')

    # OpenStack
    OS_AUTH_URL = os.getenv('OS_AUTH_URL')
    OS_USERNAME = os.getenv('OS_USERNAME')
    OS_PASSWORD = os.getenv('OS_PASSWORD')
    OS_PROJECT_NAME = os.getenv('OS_PROJECT_NAME')
    OS_USER_DOMAIN_NAME = os.getenv('OS_USER_DOMAIN_NAME', 'Default')
    OS_PROJECT_DOMAIN_NAME = os.getenv('OS_PROJECT_DOMAIN_NAME', 'Default')

    # Securite
    SECRET_TOKEN = os.getenv('SECRET_TOKEN', 'heat-secret-token')
    SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', 7200))
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    LOCKOUT_DURATION = int(os.getenv('LOCKOUT_DURATION', 300))

    # Scaling
    DEFAULT_SCALE_UP_THRESHOLD = int(os.getenv('DEFAULT_SCALE_UP_THRESHOLD', 80))
    DEFAULT_SCALE_DOWN_THRESHOLD = int(os.getenv('DEFAULT_SCALE_DOWN_THRESHOLD', 20))
    COOLDOWN_SECONDS = int(os.getenv('COOLDOWN_SECONDS', 120))

    # Logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    # Metriques disponibles avec configuration detaillee
    AVAILABLE_METRICS = {
        'cpu': {
            'name': 'CPU',
            'unit': '%',
            'description': 'Utilisation processeur',
            'min': 0,
            'max': 100,
            'default_enabled': True,
            'default_threshold_up': 80,
            'default_threshold_down': 20
        },
        'ram': {
            'name': 'RAM',
            'unit': '%',
            'description': 'Utilisation memoire',
            'min': 0,
            'max': 100,
            'default_enabled': True,
            'default_threshold_up': 85,
            'default_threshold_down': 30
        },
        'disk': {
            'name': 'Disque',
            'unit': '%',
            'description': 'Utilisation espace disque',
            'min': 0,
            'max': 100,
            'default_enabled': True,
            'default_threshold_up': 90,
            'default_threshold_down': 40
        },
        'network_in': {
            'name': 'Reseau Entrant',
            'unit': 'Mbps',
            'description': 'Bande passante entrante',
            'min': 0,
            'max': None,
            'default_enabled': False,
            'default_threshold_up': 100,
            'default_threshold_down': 10
        },
        'network_out': {
            'name': 'Reseau Sortant',
            'unit': 'Mbps',
            'description': 'Bande passante sortante',
            'min': 0,
            'max': None,
            'default_enabled': False,
            'default_threshold_up': 100,
            'default_threshold_down': 10
        },
        'network_latency': {
            'name': 'Latence Reseau',
            'unit': 'ms',
            'description': 'Latence reseau moyenne',
            'min': 0,
            'max': None,
            'default_enabled': False,
            'default_threshold_up': 200,
            'default_threshold_down': 20
        }
    }

    @classmethod
    def validate(cls):
        """Valider que les variables critiques sont definies"""
        errors = []

        if not cls.OS_AUTH_URL:
            errors.append("OS_AUTH_URL non defini dans .env")
        if not cls.OS_USERNAME:
            errors.append("OS_USERNAME non defini dans .env")
        if not cls.OS_PASSWORD:
            errors.append("OS_PASSWORD non defini dans .env")
        if not cls.OS_PROJECT_NAME:
            errors.append("OS_PROJECT_NAME non defini dans .env")

        if errors:
            raise ValueError(f"Configuration invalide:\n" + "\n".join(f"- {e}" for e in errors))

        return True


# Dashboard IP pour les agents VM
DASHBOARD_IP = os.getenv('DASHBOARD_IP', 'auto')

@staticmethod
def get_dashboard_ip():
    """
    Obtenir l'IP du dashboard pour les agents VM

    Returns:
        str: IP du serveur dashboard
    """
    if Config.DASHBOARD_IP != 'auto':
        return Config.DASHBOARD_IP

    # Auto-detection de l'IP
    import socket
    try:
        # Methode 1: Connexion vers Internet pour trouver l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Methode 2: Fallback vers localhost
        return "127.0.0.1"
