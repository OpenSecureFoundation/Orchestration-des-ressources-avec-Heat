# import os
# from app import create_app
# from app.controllers.api_routes import api_bp

# # 1. Création de l'application via la factory
# app = create_app()

# # 2. Enregistrement des routes API
# app.register_blueprint(api_bp)

# # 3. Route pour servir le Frontend (React)
# @app.route('/')
# def serve_index():
#     # On cherche le fichier index.html à la racine
#     return app.send_static_file('../index.html')

# if __name__ == "__main__":
#     # On crée le dossier de logs s'il n'existe pas
#     if not os.path.exists('logs'):
#         os.makedirs('logs')
        
#     print("🚀 Démarrage du Smart Scaling Dashboard...")
#     print("🔗 API accessible sur http://0.0.0.0:8765")
    
#     # Lancement du serveur (threaded=True est crucial pour le scaler)
#     app.run(host="0.0.0.0", port=8765, debug=True, threaded=True)


import os
import sys
from flask import Flask
from flask_cors import CORS
from config.settings import Config
from app.models.openstack_client import OpenStackClient
from app.models.heat_manager import HeatManager
from app.controllers.scaling_manager import ScalingManager
from app.views.api_routes import api_bp

def start_application():
    """
    Initialisation globale selon le Cahier de Conception.
    Garantit l'isolation des composants et la sécurité Keystone.
    """
    app = Flask(__name__)
    
    # Activation du CORS pour autoriser le Frontend React (indispensable pour éviter NetworkError)
    CORS(app)
    
    # 1. Création des répertoires nécessaires (Logs/Audit pour la traçabilité SSI)
    if not os.path.exists('logs'):
        os.makedirs('logs')

    print("--- Initialisation du Système Smart Scaling ---")

    try:
        # 2. Instanciation du Modèle (Connexion OpenStack)
        # Vérifie les identifiants dans config/settings.py
        os_client = OpenStackClient()
        print("✅ Connexion Keystone établie avec succès.")
        
        # 3. Instanciation des Gestionnaires (Orchestration & Décision)
        heat_mgr = HeatManager(os_client)
        scaler_mgr = ScalingManager(os_client)

        # 4. Injection des instances dans la configuration Flask
        # Évite de recréer des connexions à chaque requête API
        app.config['OS_CLIENT'] = os_client
        app.config['HEAT_MANAGER'] = heat_mgr
        app.config['SCALING_MANAGER'] = scaler_mgr

        # 5. Enregistrement des Routes avec le préfixe /api
        # URL finale : http://localhost:8765/api/stacks
        app.register_blueprint(api_bp, url_prefix='/api')

        print("✅ Tous les modules sont chargés (MVC respecté).")
        
    except Exception as e:
        print(f"❌ Erreur critique lors du démarrage : {e}")
        sys.exit(1)

    return app

# Point d'entrée conforme au diagramme de déploiement
if __name__ == "__main__":
    application = start_application()
    
    # threaded=True est OBLIGATOIRE pour permettre au monitoring CPU 
    # de tourner en arrière-plan sans bloquer l'interface.
    application.run(
        host="0.0.0.0", 
        port=8765, 
        debug=True, 
        threaded=True
    )