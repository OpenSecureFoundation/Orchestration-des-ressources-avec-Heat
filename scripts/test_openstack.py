#!/usr/bin/env python3
"""
Script de verification de la connexion OpenStack.
Lance apres l'installation pour valider la configuration.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.config import Config


def tester_connexion():
    """Teste la connexion a chaque service OpenStack."""
    print("=" * 55)
    print("  Test de connexion OpenStack")
    print("=" * 55)
    print(f"  Auth URL : {Config.OS_AUTH_URL}")
    print(f"  Projet   : {Config.OS_PROJECT_NAME}")
    print(f"  User     : {Config.OS_USERNAME}")
    print("=" * 55)

    erreurs = []

    # Test Keystone
    try:
        from backend.services.openstack_service import OpenStackService
        sess = OpenStackService._get_session()
        token = sess.get_token()
        print(f"  Keystone (auth)    : OK - token obtenu")
    except Exception as e:
        print(f"  Keystone (auth)    : ERREUR - {e}")
        erreurs.append("Keystone")
        return erreurs

    # Test Nova
    try:
        nc = OpenStackService.get_nova_client()
        flavors = nc.flavors.list()
        print(f"  Nova (compute)     : OK - {len(list(flavors))} flavors")
    except Exception as e:
        print(f"  Nova (compute)     : ERREUR - {e}")
        erreurs.append("Nova")

    # Test Neutron
    try:
        nc = OpenStackService.get_neutron_client()
        reseaux = nc.list_networks()
        print(f"  Neutron (reseau)   : OK - {len(reseaux['networks'])} reseaux")
    except Exception as e:
        print(f"  Neutron (reseau)   : ERREUR - {e}")
        erreurs.append("Neutron")

    # Test Heat
    try:
        hc = OpenStackService.get_heat_client()
        stacks = list(hc.stacks.list())
        print(f"  Heat (orchestr.)   : OK - {len(stacks)} stacks")
    except Exception as e:
        print(f"  Heat (orchestr.)   : ERREUR - {e}")
        erreurs.append("Heat")

    # Detection IP
    ip = Config.get_dashboard_ip()
    print(f"  IP Dashboard       : {ip}")

    print("=" * 55)
    if erreurs:
        print(f"  ECHECS : {', '.join(erreurs)}")
        print("  Verifiez vos credentials dans .env")
    else:
        print("  Tous les services sont accessibles.")
    print("=" * 55)

    return erreurs


if __name__ == "__main__":
    erreurs = tester_connexion()
    sys.exit(1 if erreurs else 0)
