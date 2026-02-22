# import openstack
# from datetime import datetime, timedelta, timezone
# from config.settings import AUTH_CONFIG, FLAVOR_SEQUENCE

# class OpenStackManager:
#     def __init__(self):
#         """Initialise la connexion avec Keystone via OpenStackSDK"""
#         try:
#             self.conn = openstack.connect(**AUTH_CONFIG)
#             print("✅ Connexion Keystone réussie.")
#         except Exception as e:
#             print(f"❌ Erreur de connexion Keystone : {e}")
#             raise

#     # --- GESTION DES INSTANCES (NOVA) ---
#     def get_all_servers(self):
#         """Lise les instances et enrichit avec les flavors"""
#         return list(self.conn.compute.servers(details=True))

#     def get_flavor_details(self, flavor_id):
#         return self.conn.compute.get_flavor(flavor_id)

#     # --- GESTION DU SCALING VERTICAL ---
#     def resize_instance(self, server_id, target_flavor_name):
#         """Lance l'ordre de resize vers une flavor supérieure/inférieure"""
#         # Récupération de l'ID de la flavor cible
#         target_flavor = self.conn.compute.find_flavor(target_flavor_name)
#         if not target_flavor:
#             return False, "Flavor cible introuvable"
        
#         self.conn.compute.resize_server(server_id, target_flavor.id)
#         return True, "Resize initié"

#     def confirm_resize(self, server_id):
#         """Confirme le passage définitif à la nouvelle taille"""
#         self.conn.compute.confirm_server_resize(server_id)

#     # --- GESTION DE LA TÉLÉMÉTRIE (GNOCCHI) ---
#     def get_metrics(self, resource_id, metric_name="cpu_util", window=120):
#         """Récupère les mesures moyennes depuis Gnocchi"""
#         now = datetime.now(tz=timezone.utc)
#         start = now - timedelta(seconds=window)
#         try:
#             measures = self.conn.metric.get_measures(
#                 metric=metric_name,
#                 resource_id=resource_id,
#                 start=start.isoformat(),
#                 stop=now.isoformat(),
#             )
#             if not measures: return 0.0, []
            
#             values = [m[2] for m in measures if m[2] is not None]
#             avg = round(sum(values) / len(values), 2) if values else 0.0
#             history = [{"time": str(m[0]), "val": m[2]} for m in measures]
#             return avg, history
#         except Exception:
#             return 0.0, []

#     # --- GESTION DE L'ORCHESTRATION (HEAT) ---
#     def get_stacks(self):
#         """Récupère les infrastructures Multi-VM (Heat Stacks)"""
#         return list(self.conn.orchestration.stacks())