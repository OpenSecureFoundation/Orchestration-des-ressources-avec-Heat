#!/usr/bin/env python3
"""
Script d'initialisation de la base de donnees
Cree les tables et charge les templates builtin
"""

import sys
import os

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models.database import Database
from backend.services.template_service import TemplateService
from backend.config import Config

def main():
    """Initialiser la base de donnees"""
    print("Initialisation de la base de donnees...")

    # Initialiser la base
    Database.initialize(Config.DATABASE_PATH)
    print(f"Base de donnees creee: {Config.DATABASE_PATH}")

    # Charger les templates builtin
    print("\nChargement des templates builtin...")
    count = TemplateService.load_builtin_templates()
    print(f"{count} templates builtin charges")

    print("\nInitialisation terminee avec succes!")

if __name__ == '__main__':
    main()
