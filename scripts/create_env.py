#!/usr/bin/env python3
"""
Script interactif pour creer le fichier .env
Execute ce script pour configurer ton environnement
"""

import os

def ask_question(question, default=None, required=True):
    """Poser une question et retourner la reponse"""
    if default:
        prompt = f"{question} [{default}]: "
    else:
        prompt = f"{question}: "

    while True:
        answer = input(prompt).strip()

        if answer:
            return answer
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("Cette valeur est obligatoire !")

def main():
    print("=" * 60)
    print("CONFIGURATION DE L'ENVIRONNEMENT HEAT ORCHESTRATION")
    print("=" * 60)
    print()
    print("Ce script va creer le fichier .env avec tes parametres.")
    print()

    # Variables OpenStack
    print("--- CONFIGURATION OPENSTACK ---")
    print("Ces informations se trouvent dans ton fichier ~/admin-openrc")
    print()

    os_auth_url = ask_question(
        "OS_AUTH_URL (URL Keystone)",
        default="http://localhost:5000/v3"
    )

    os_username = ask_question(
        "OS_USERNAME (nom utilisateur OpenStack)",
        default="admin"
    )

    os_password = ask_question(
        "OS_PASSWORD (mot de passe OpenStack)",
        default="admin"
    )

    os_project_name = ask_question(
        "OS_PROJECT_NAME (nom du projet)",
        default="admin"
    )

    os_user_domain = ask_question(
        "OS_USER_DOMAIN_NAME",
        default="Default"
    )

    os_project_domain = ask_question(
        "OS_PROJECT_DOMAIN_NAME",
        default="Default"
    )

    # Variables Flask
    print()
    print("--- CONFIGURATION FLASK ---")
    print()

    flask_secret = ask_question(
        "FLASK_SECRET_KEY (cle secrete Flask)",
        default="dev-secret-key-change-in-production"
    )

    flask_debug = ask_question(
        "FLASK_DEBUG (True/False)",
        default="True"
    )

    flask_port = ask_question(
        "FLASK_PORT (port du serveur)",
        default="8080"
    )

    # Variables de securite
    print()
    print("--- CONFIGURATION SECURITE ---")
    print()

    secret_token = ask_question(
        "SECRET_TOKEN (token pour agents VM)",
        default="heat-secret-token"
    )

    # Variables scaling
    print()
    print("--- CONFIGURATION SCALING ---")
    print()

    scale_up = ask_question(
        "DEFAULT_SCALE_UP_THRESHOLD (%)",
        default="80"
    )

    scale_down = ask_question(
        "DEFAULT_SCALE_DOWN_THRESHOLD (%)",
        default="20"
    )

    cooldown = ask_question(
        "COOLDOWN_SECONDS (secondes)",
        default="120"
    )

    # Generer le fichier .env
    print()
    print("Création du fichier .env...")

    env_content = f"""# ============================================================
# CONFIGURATION OPENSTACK
# ============================================================
OS_AUTH_URL={os_auth_url}
OS_USERNAME={os_username}
OS_PASSWORD={os_password}
OS_PROJECT_NAME={os_project_name}
OS_USER_DOMAIN_NAME={os_user_domain}
OS_PROJECT_DOMAIN_NAME={os_project_domain}

# ============================================================
# CONFIGURATION APPLICATION
# ============================================================
FLASK_SECRET_KEY={flask_secret}
FLASK_DEBUG={flask_debug}
FLASK_PORT={flask_port}
FLASK_HOST=0.0.0.0

# ============================================================
# BASE DE DONNÉES
# ============================================================
DATABASE_PATH=database/orchestration.db

# ============================================================
# TEMPLATES
# ============================================================
BUILTIN_TEMPLATES_PATH=templates_storage/builtin
USER_TEMPLATES_PATH=templates_storage/user

# ============================================================
# SÉCURITÉ
# ============================================================
SECRET_TOKEN={secret_token}
SESSION_LIFETIME=7200
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=300

# ============================================================
# SCALING
# ============================================================
DEFAULT_SCALE_UP_THRESHOLD={scale_up}
DEFAULT_SCALE_DOWN_THRESHOLD={scale_down}
COOLDOWN_SECONDS={cooldown}

# ============================================================
# LOGS
# ============================================================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""

    # Determiner le chemin du fichier .env
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_path = os.path.join(project_root, '.env')

    # Verifier si .env existe deja
    if os.path.exists(env_path):
        overwrite = ask_question(
            "Le fichier .env existe deja. Ecraser ? (oui/non)",
            default="non",
            required=False
        )

        if overwrite.lower() not in ['oui', 'o', 'yes', 'y']:
            print("Annulation.")
            return

    # Ecrire le fichier
    with open(env_path, 'w') as f:
        f.write(env_content)

    print()
    print("✓ Fichier .env cree avec succes !")
    print(f"  Chemin: {env_path}")
    print()
    print("PROCHAINES ETAPES:")
    print("1. Verifier le fichier .env et ajuster si necessaire")
    print("2. Executer: python3 scripts/setup_database.py")
    print("3. Executer: python3 scripts/create_admin.py")
    print("4. Lancer l'application: python3 run.py")
    print()

if __name__ == '__main__':
    main()
