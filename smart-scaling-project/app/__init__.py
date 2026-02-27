# from flask import Flask
# from flask_cors import CORS
# from app.models.openstack_manager import OpenStackManager
# from app.controllers.scaling_engine import ScalingEngine

# # On initialise les composants globaux
# # Le Modèle (Connexion Keystone)
# try:
#     model_shared = OpenStackManager()
# except Exception:
#     model_shared = None

# # Le Contrôleur (Moteur de Scaling)
# scaler_shared = ScalingEngine(model_shared)

# def create_app():
#     """Factory function pour créer l'instance Flask"""
#     app = Flask(__name__)
#     CORS(app)  # Autorise le Frontend React à parler au Backend
    
#     # Injection des instances dans le contexte de l'app pour les routes
#     app.config['MODEL'] = model_shared
#     app.config['SCALER'] = scaler_shared

#     return app

from flask import Flask
from flask_cors import CORS
# On importe OpenStackClient (le nom validé pour ton projet SSI)
from app.models.openstack_client import OpenStackClient
from app.controllers.scaling_manager import ScalingManager
from app.models.heat_manager import HeatManager

def create_app():
    """Factory function pour initialiser l'application Flask"""
    app = Flask(__name__)
    CORS(app) # Autorise le futur Frontend React
    
    # 1. Initialisation du client OpenStack (Modèle)
    os_client = OpenStackClient()
    
    # 2. Initialisation des gestionnaires
    heat_mgr = HeatManager(os_client)
    scaler_mgr = ScalingManager(os_client)

    # 3. Stockage dans la config Flask pour les routes
    app.config['OS_CLIENT'] = os_client
    app.config['HEAT_MANAGER'] = heat_mgr
    app.config['SCALING_MANAGER'] = scaler_mgr

    return app