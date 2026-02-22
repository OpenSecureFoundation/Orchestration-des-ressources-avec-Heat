# class HeatManager:
#     def __init__(self, openstack_conn):
#         self.conn = openstack_conn

#     def list_infrastructures(self):
#         """Récupère tous les déploiements Multi-VM"""
#         return list(self.conn.orchestration.stacks())

#     def get_stack_resources(self, stack_name_or_id):
#         """Liste toutes les VMs et réseaux créés par un template Heat"""
#         resources = self.conn.orchestration.resources(stack_name_or_id)
#         return [{
#             "name": r.resource_name,
#             "type": r.resource_type,
#             "status": r.resource_status,
#             "physical_id": r.physical_resource_id
#         } for r in resources]


from app.models.openstack_client import OpenStackClient

class HeatManager:
    """
    Gestionnaire d'Orchestration Heat.
    Répond au besoin : 'Création automatisée d'architectures complètes'.
    """

    def __init__(self, os_client):
        # On réutilise la connexion sécurisée du client principal
        self.conn = os_client.conn

    def list_stacks(self):
        """Liste les infrastructures multi-VM (Stacks)"""
        return list(self.conn.orchestration.stacks())

    def get_stack_details(self, stack_name_or_id):
        """Récupère les détails d'un déploiement spécifique"""
        return self.conn.orchestration.get_stack(stack_name_or_id)

    def get_stack_resources(self, stack_name_or_id):
            """
            Liste les ressources d'un Stack avec une vérification 
            stricte des attributs du SDK OpenStack.
            """
            # Récupération des ressources via le SDK
            resources = self.conn.orchestration.resources(stack_name_or_id)
            
            formatted_resources = []
            for r in resources:
                # On utilise getattr(objet, 'nom_attribut', valeur_par_defaut)
                # Cela empêche l'erreur "AttributeError" si le nom change
                formatted_resources.append({
                    "name": getattr(r, 'name', getattr(r, 'resource_name', "Inconnu")),
                    "type": getattr(r, 'resource_type', "Type inconnu"),
                    "physical_id": getattr(r, 'physical_resource_id', None),
                    "status": getattr(r, 'status', getattr(r, 'resource_status', "N/A"))
                })
                
            return formatted_resources

    def delete_infrastructure(self, stack_name_or_id):
        """Supprime toute l'infrastructure proprement"""
        return self.conn.orchestration.delete_stack(stack_name_or_id)