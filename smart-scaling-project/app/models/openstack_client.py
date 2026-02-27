import openstack
from config.settings import Config
import logging

# Configuration du logger pour la traçabilité (Besoin SSI : Audit)
logging.basicConfig(filename=Config.LOG_FILE, level=logging.INFO)

class OpenStackClient:
    """
    Composant d'exécution : Assure la communication avec Nova, Heat et Gnocchi.
    Répond au cas d'utilisation : 'Surveillance Métrique' et 'Scaling'.
    """

    def __init__(self):
        try:
            # Authentification via Keystone (Gestion de session sécurisée)
            self.conn = openstack.connect(
                auth_url=Config.AUTH_URL,
                username=Config.USERNAME,
                password=Config.PASSWORD,
                project_name=Config.PROJECT_NAME,
                user_domain_name=Config.USER_DOMAIN_NAME,
                project_domain_name=Config.PROJECT_DOMAIN_NAME,
                region_name="RegionOne"
            )
            print("✅ Connexion Keystone établie avec succès.")
        except Exception as e:
            logging.error(f"Échec Auth Keystone : {e}")
            raise

    # --- Section Orchestration (Heat) ---
    def get_stack_list(self):
        """Récupère les stacks (Cas d'utilisation : Déploiement Complexe)"""
        return list(self.conn.orchestration.stacks())

    # --- Section Scaling Vertical (Nova) ---
    def get_server_details(self, server_id):
        """Récupère l'état et la flavor actuelle d'une VM"""
        return self.conn.compute.get_server(server_id)

    def trigger_resize(self, server_id, target_flavor_name):
        """
        Exécute le changement de gabarit (Scaling Vertical).
        Action : Resize -> Confirm
        """
        flavor = self.conn.compute.find_flavor(target_flavor_name)
        if flavor:
            self.conn.compute.resize_server(server_id, flavor.id)
            logging.info(f"Scaling initié pour {server_id} vers {target_flavor_name}")
            return True
        return False

    def confirm_resize(self, server_id):
        """Confirme l'opération de resize pour finaliser le scaling"""
        self.conn.compute.confirm_server_resize(server_id)
        logging.info(f"Scaling confirmé pour {server_id}")

    # --- Section Télémétrie (Monitoring) ---
    def fetch_cpu_metrics(self, resource_id):
        """
        Récupère les données de charge (Cas d'utilisation : Surveillance Métrique).
        Utilise Gnocchi pour extraire la moyenne CPU sur la fenêtre définie.
        """
        # Note : On peut ici basculer sur Prometheus comme évoqué dans ton cahier
        # Pour l'instant on garde la compatibilité Gnocchi de ton code original
        try:
            measures = self.conn.metric.get_measures(
                metric="cpu_util",
                resource_id=resource_id,
                limit=5
            )
            if measures:
                # Calcul de la moyenne des dernières mesures
                values = [m[2] for m in measures]
                return sum(values) / len(values)
            return 0
        except Exception as e:
            logging.error(f"Erreur monitoring {resource_id}: {e}")
            return None