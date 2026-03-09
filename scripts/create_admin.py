#!/usr/bin/env python3
"""
Script de creation d'un utilisateur administrateur
"""

import sys
import os
import getpass

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models.database import Database
from backend.models.user import User
from backend.config import Config

def main():
    """Creer un utilisateur administrateur"""
    print("Creation d'un utilisateur administrateur\n")

    # Initialiser la base
    Database.initialize(Config.DATABASE_PATH)

    # Demander les informations
    username = input("Nom d'utilisateur (admin): ").strip() or 'admin'

    # Verifier si l'utilisateur existe deja
    existing = User.get_by_id(1)  # Premier utilisateur
    if existing and existing['username'] == username:
        print(f"\nL'utilisateur '{username}' existe deja.")
        response = input("Voulez-vous reinitialiser son mot de passe ? (o/n): ")
        if response.lower() != 'o':
            print("Annulation.")
            return

    password = getpass.getpass("Mot de passe: ")
    password_confirm = getpass.getpass("Confirmer le mot de passe: ")

    if password != password_confirm:
        print("\nErreur: Les mots de passe ne correspondent pas")
        sys.exit(1)

    full_name = input("Nom complet (optionnel): ").strip() or None
    email = input("Email (optionnel): ").strip() or None

    # Creer l'utilisateur
    try:
        user_id = User.create(
            username=username,
            password=password,
            role='admin',
            full_name=full_name,
            email=email
        )

        print(f"\nUtilisateur administrateur cree avec succes!")
        print(f"ID: {user_id}")
        print(f"Username: {username}")
        print(f"Role: admin")

    except Exception as e:
        print(f"\nErreur lors de la creation: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
