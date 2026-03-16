"""
Configuration centrale de l'application.
Charge les variables depuis .env et detecte automatiquement
les parametres de l'environnement OpenStack.
"""

import os
import socket
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

# Chargement du fichier .env
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Configuration principale de l'application."""

    # ---- Flask ----
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())
    DEBUG = FLASK_ENV == "development"

    # ---- Dashboard ----
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8080))

    # ---- OpenStack credentials ----
    OS_AUTH_URL = os.getenv("OS_AUTH_URL", "http://controller:5000/v3")
    OS_USERNAME = os.getenv("OS_USERNAME", "admin")
    OS_PASSWORD = os.getenv("OS_PASSWORD", "")
    OS_PROJECT_NAME = os.getenv("OS_PROJECT_NAME", "admin")
    OS_USER_DOMAIN_NAME = os.getenv("OS_USER_DOMAIN_NAME", "Default")
    OS_PROJECT_DOMAIN_NAME = os.getenv("OS_PROJECT_DOMAIN_NAME", "Default")

    # ---- Reseaux ----
    PUBLIC_NETWORK_NAME = os.getenv("PUBLIC_NETWORK_NAME", "public-network")
    PRIVATE_NETWORK_NAME = os.getenv("PRIVATE_NETWORK_NAME", "private-network")

    # ---- Images et flavors ----
    DEFAULT_IMAGE = os.getenv("DEFAULT_IMAGE", "ubuntu-22.04")
    DEFAULT_FLAVOR = os.getenv("DEFAULT_FLAVOR", "m1.small")

    # ---- Monitoring ----
    METRICS_INTERVAL = int(os.getenv("METRICS_INTERVAL", 30))
    SCALING_COOLDOWN = int(os.getenv("SCALING_COOLDOWN", 60))

    # ---- Base de donnees ----
    # Chemin absolu pour eviter les problemes de repertoire courant
    BASE_DIR = Path(__file__).parent.parent
    _db_path_relative = os.getenv("DATABASE_PATH", "database/orchestration.db")
    DATABASE_PATH = str(BASE_DIR / _db_path_relative)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Logs ----
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    _log_path_relative = os.getenv("LOG_FILE", "logs/orchestration.log")
    LOG_FILE = str(BASE_DIR / _log_path_relative)

    # ---- Repertoires ----
    TEMPLATES_BUILTIN_DIR = BASE_DIR / "templates_storage" / "builtin"
    TEMPLATES_USER_DIR = BASE_DIR / "templates_storage" / "user"
    DATABASE_DIR = BASE_DIR / "database"
    LOGS_DIR = BASE_DIR / "logs"

    @staticmethod
    def get_dashboard_ip() -> str:
        """
        Detecte automatiquement l'IP du dashboard.

        Strategies dans l'ordre :
        1. Variable DASHBOARD_IP dans .env (si != 'auto')
        2. Connexion socket UDP vers 8.8.8.8 (recupere l'IP locale)
        3. Parsing de 'ip addr show' pour trouver l'IP sur br-ex
        4. Fallback sur 127.0.0.1
        """
        dashboard_ip_env = os.getenv("DASHBOARD_IP", "auto")

        # Strategie 1 : valeur explicite dans .env
        if dashboard_ip_env and dashboard_ip_env.lower() != "auto":
            logger.info(f"IP dashboard depuis .env : {dashboard_ip_env}")
            return dashboard_ip_env

        # Strategie 2 : connexion UDP pour obtenir l'IP locale
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            if ip and ip != "0.0.0.0":
                logger.info(f"IP dashboard detectee via socket : {ip}")
                return ip
        except Exception as e:
            logger.debug(f"Detection socket echouee : {e}")

        # Strategie 3 : lecture de l'interface br-ex
        try:
            result = subprocess.run(
                ["ip", "addr", "show", "br-ex"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("inet ") and "scope global" in line:
                    ip = line.split()[1].split("/")[0]
                    logger.info(f"IP dashboard detectee via br-ex : {ip}")
                    return ip
        except Exception as e:
            logger.debug(f"Detection br-ex echouee : {e}")

        # Strategie 4 : fallback
        logger.warning("IP dashboard non detectee, utilisation de 127.0.0.1")
        return "127.0.0.1"

    @staticmethod
    def resolve_hostname(url: str) -> str:
        """
        Resout 'controller' en IP si necessaire.
        Utile pour les environnements ou OpenStack utilise
        'controller' comme hostname sans entree DNS.
        """
        if "controller" not in url:
            return url

        try:
            ip = socket.gethostbyname("controller")
            resolved = url.replace("controller", ip)
            logger.debug(f"Hostname 'controller' resolu en : {ip}")
            return resolved
        except socket.gaierror:
            # 'controller' n'est pas resolvable, on retourne l'URL d'origine
            logger.debug("Hostname 'controller' non resolvable, URL inchangee")
            return url

    @staticmethod
    def get_openstack_credentials() -> dict:
        """
        Retourne le dictionnaire de credentials OpenStack
        pret pour les clients keystoneauth1.
        """
        return {
            "auth_url": Config.OS_AUTH_URL,
            "username": Config.OS_USERNAME,
            "password": Config.OS_PASSWORD,
            "project_name": Config.OS_PROJECT_NAME,
            "user_domain_name": Config.OS_USER_DOMAIN_NAME,
            "project_domain_name": Config.OS_PROJECT_DOMAIN_NAME,
        }

    @staticmethod
    def validate() -> None:
        """
        Verifie que tous les parametres requis sont presents.
        Cree les repertoires necessaires.
        Leve une exception si la configuration est invalide.
        """
        erreurs = []

        # Verification des parametres obligatoires
        if not Config.OS_AUTH_URL:
            erreurs.append("OS_AUTH_URL manquant")
        if not Config.OS_USERNAME:
            erreurs.append("OS_USERNAME manquant")
        if not Config.OS_PASSWORD:
            erreurs.append("OS_PASSWORD manquant")
        if not Config.OS_PROJECT_NAME:
            erreurs.append("OS_PROJECT_NAME manquant")

        if erreurs:
            raise ValueError(
                f"Configuration invalide : {', '.join(erreurs)}. "
                "Verifiez votre fichier .env"
            )

        # Creation des repertoires avec permissions correctes
        for repertoire in [Config.DATABASE_DIR, Config.LOGS_DIR,
                           Config.TEMPLATES_USER_DIR, Config.TEMPLATES_BUILTIN_DIR]:
            repertoire.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(str(repertoire), 0o775)
            except Exception:
                pass

        # Verification que la BDD est accessible en ecriture
        db_path = Path(Config.DATABASE_PATH)
        if db_path.exists():
            try:
                os.chmod(str(db_path), 0o664)
            except Exception:
                pass

        logger.info("Configuration validee avec succes")

    @staticmethod
    def setup_logging() -> None:
        """Configure le systeme de logging de l'application."""
        Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        niveau = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)

        logging.basicConfig(
            level=niveau,
            format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
