#!/usr/bin/env python3
"""
Detection automatique de l'environnement OpenStack.
Genere le fichier .env configure pour l'environnement courant.
"""

import os
import socket
import subprocess
import sys


def detect_dashboard_ip() -> str:
    """Detecte l'IP de la machine sur le reseau externe (br-ex)."""
    # Methode 1 : socket UDP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != "0.0.0.0":
            return ip
    except Exception:
        pass

    # Methode 2 : interface br-ex
    try:
        result = subprocess.run(
            ["ip", "addr", "show", "br-ex"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet ") and "scope global" in line:
                return line.split()[1].split("/")[0]
    except Exception:
        pass

    return "127.0.0.1"


def detect_openstack_creds() -> dict:
    """Lit les credentials OpenStack depuis admin-openrc ou variables d'env."""
    creds = {
        "OS_AUTH_URL": os.getenv("OS_AUTH_URL", "http://controller:5000/v3"),
        "OS_USERNAME": os.getenv("OS_USERNAME", "admin"),
        "OS_PASSWORD": os.getenv("OS_PASSWORD", ""),
        "OS_PROJECT_NAME": os.getenv("OS_PROJECT_NAME", "admin"),
        "OS_USER_DOMAIN_NAME": os.getenv("OS_USER_DOMAIN_NAME", "Default"),
        "OS_PROJECT_DOMAIN_NAME": os.getenv("OS_PROJECT_DOMAIN_NAME", "Default"),
    }

    # Tentative de lecture du fichier admin-openrc
    openrc_path = os.path.expanduser("~/admin-openrc")
    if os.path.exists(openrc_path):
        with open(openrc_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    partie = line[7:]
                    if "=" in partie:
                        cle, valeur = partie.split("=", 1)
                        creds[cle.strip()] = valeur.strip()

    return creds


def detect_networks() -> dict:
    """Detecte les noms des reseaux public et prive."""
    reseaux = {"public": "public-network", "prive": "private-network"}

    try:
        result = subprocess.run(
            ["openstack", "network", "list", "--external", "-f", "value", "-c", "Name"],
            capture_output=True, text=True, timeout=15
        )
        lignes = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if lignes:
            reseaux["public"] = lignes[0]
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["openstack", "network", "list", "-f", "value", "-c", "Name"],
            capture_output=True, text=True, timeout=15
        )
        for nom in result.stdout.splitlines():
            nom = nom.strip()
            if nom and nom != reseaux["public"]:
                reseaux["prive"] = nom
                break
    except Exception:
        pass

    return reseaux


def detect_default_image() -> str:
    """Detecte l'image Ubuntu disponible ou retourne la premiere."""
    try:
        result = subprocess.run(
            ["openstack", "image", "list", "--status", "active", "-f", "value", "-c", "Name"],
            capture_output=True, text=True, timeout=15
        )
        images = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        for img in images:
            if "ubuntu" in img.lower():
                return img
        if images:
            return images[0]
    except Exception:
        pass
    return "ubuntu-22.04"


def generate_env_file(chemin: str = ".env") -> None:
    """Genere le fichier .env avec les valeurs detectees."""
    print("Detection de l'environnement en cours...")

    dashboard_ip = detect_dashboard_ip()
    print(f"  IP Dashboard       : {dashboard_ip}")

    creds = detect_openstack_creds()
    print(f"  Auth URL           : {creds['OS_AUTH_URL']}")
    print(f"  Utilisateur        : {creds['OS_USERNAME']}")

    reseaux = detect_networks()
    print(f"  Reseau public      : {reseaux['public']}")
    print(f"  Reseau prive       : {reseaux['prive']}")

    image = detect_default_image()
    print(f"  Image par defaut   : {image}")

    # Demande du mot de passe si absent
    password = creds.get("OS_PASSWORD", "")
    if not password:
        password = input("\nMot de passe OpenStack (OS_PASSWORD) : ").strip()

    import secrets
    secret_key = secrets.token_hex(24)

    contenu = f"""# ============================================================
# Configuration generee automatiquement par detect_environment.py
# ============================================================

# Application Flask
FLASK_ENV=development
SECRET_KEY={secret_key}

# IP du dashboard (detectee automatiquement)
DASHBOARD_IP={dashboard_ip}
DASHBOARD_PORT=8080

# Credentials OpenStack
OS_AUTH_URL={creds['OS_AUTH_URL']}
OS_USERNAME={creds['OS_USERNAME']}
OS_PASSWORD={password}
OS_PROJECT_NAME={creds['OS_PROJECT_NAME']}
OS_USER_DOMAIN_NAME={creds['OS_USER_DOMAIN_NAME']}
OS_PROJECT_DOMAIN_NAME={creds['OS_PROJECT_DOMAIN_NAME']}
OS_IDENTITY_API_VERSION=3
OS_IMAGE_API_VERSION=2

# Reseaux
PUBLIC_NETWORK_NAME={reseaux['public']}
PRIVATE_NETWORK_NAME={reseaux['prive']}

# Images et flavors par defaut
DEFAULT_IMAGE={image}
DEFAULT_FLAVOR=m1.small

# Monitoring
METRICS_INTERVAL=30
SCALING_COOLDOWN=60

# Base de donnees
DATABASE_PATH=database/orchestration.db

# Logs
LOG_LEVEL=INFO
LOG_FILE=logs/orchestration.log
"""

    with open(chemin, "w") as f:
        f.write(contenu)

    print(f"\nFichier {chemin} genere avec succes.")


if __name__ == "__main__":
    chemin_env = sys.argv[1] if len(sys.argv) > 1 else ".env"
    generate_env_file(chemin_env)
