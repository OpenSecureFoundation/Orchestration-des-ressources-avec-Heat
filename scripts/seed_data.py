#!/usr/bin/env python3
"""
Script pour peupler la base de donnees avec des donnees de test
"""

import sys
import os

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models.database import Database
from backend.models.user import User
from backend.models.metrics import ScalingPolicy
from backend.config import Config

def main():
    """Peupler la base avec des donnees de test"""
    print("Peuplement de la base de donnees avec des donnees de test...\n")

    # Initialiser la base
    Database.initialize(Config.DATABASE_PATH)

    # Creer un utilisateur de test
    print("Creation d'utilisateurs de test...")

    try:
        # Admin
        admin_id = User.create(
            username='admin',
            password='admin123',
            role='admin',
            full_name='Administrateur',
            email='admin@example.com'
        )
        print(f"  Admin cree (ID: {admin_id})")

        # User normal
        user_id = User.create(
            username='user',
            password='user123',
            role='user',
            full_name='Utilisateur Test',
            email='user@example.com'
        )
        print(f"  User cree (ID: {user_id})")

    except Exception as e:
        print(f"  Utilisateurs deja existants ou erreur: {str(e)}")

    print("\nDonnees de test creees avec succes!")
    print("\nComptes disponibles:")
    print("  - admin / admin123 (role: admin)")
    print("  - user / user123 (role: user)")

if __name__ == '__main__':
    main()
