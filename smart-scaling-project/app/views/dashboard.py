# from flask import jsonify

# class DashboardView:
#     @staticmethod
#     def render_instances(instances, monitored_ids):
#         """Formate la liste des VMs avec leur état de monitoring"""
#         formatted = []
#         for s in instances:
#             formatted.append({
#                 "id": s.id,
#                 "name": s.name,
#                 "status": s.status,
#                 "flavor": s.flavor.get('original_name') or s.flavor.get('id'),
#                 "is_monitored": s.id in monitored_ids,
#                 "addresses": s.addresses
#             })
#         return jsonify({"instances": formatted, "count": len(formatted)})

#     @staticmethod
#     def render_stacks(stacks):
#         """Formate les infrastructures Heat (Multi-VM)"""
#         return jsonify({
#             "stacks": [{
#                 "id": s.id, 
#                 "name": s.name, 
#                 "status": s.status,
#                 "created_at": s.created_at
#             } for s in stacks]
#         })

#     @staticmethod
#     def render_audit(events):
#         """Formate le journal d'audit pour l'onglet Audit du Dashboard"""
#         return jsonify({"events": list(reversed(events))})