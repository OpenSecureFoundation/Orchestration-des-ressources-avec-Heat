from flask import Blueprint, jsonify, request, current_app
import time


api_bp = Blueprint('api', __name__)

# On retire le "/api" devant chaque route car il sera ajouté par le préfixe global
@api_bp.route('/instances', methods=['GET'])
def list_instances():
    os_client = current_app.config['OS_CLIENT']
    try:
        all_vms = os_client.conn.compute.servers()
        return jsonify([{"id": s.id, "name": s.name, "status": s.status} for s in all_vms])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/stacks', methods=['GET'])
def list_stacks():
    heat_manager = current_app.config['HEAT_MANAGER']
    try:
        stacks = heat_manager.list_stacks()
        return jsonify([{"id": s.id, "name": s.name, "status": s.status} for s in stacks])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/scaler/start', methods=['POST'])
def start_scaling():
    scaling_manager = current_app.config['SCALING_MANAGER']
    data = request.json
    instance_id = data.get('instance_id')
    if not instance_id:
        return jsonify({"error": "ID d'instance manquant"}), 400
    scaling_manager.start_monitoring(instance_id)
    return jsonify({"message": f"Monitoring activé pour {instance_id}"})

@api_bp.route('/scaler/status', methods=['GET'])
def scaler_status():
    """Retourne la liste des instances actuellement sous surveillance"""
    scaling_manager = current_app.config['SCALING_MANAGER']
    return jsonify({
        "running": scaling_manager.is_running,
        "monitored_instances": list(scaling_manager.monitored_instances.keys())
    })


@api_bp.route('/stacks/<stack_id>/resources', methods=['GET'])
def get_stack_resources(stack_id):
    heat_manager = current_app.config['HEAT_MANAGER']
    try:
        # On appelle la fonction robuste qu'on vient de corriger
        data = heat_manager.get_stack_resources(stack_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/metrics/<resource_id>', methods=['GET'])
def get_metrics(resource_id):
    os_client = current_app.config['OS_CLIENT']
    
    # 1. On récupère la vraie valeur depuis ton client OpenStack
    # Cette méthode doit retourner un nombre (float)
    real_cpu_value = os_client.fetch_cpu_metrics(resource_id)
    
    # 2. On prépare le JSON avec la clé 'current_load' exigée par le Front
    return jsonify({
        "timestamp": time.time(),
        "current_load": real_cpu_value if real_cpu_value is not None else 0.0,
        "resource_id": resource_id
    })
# import time
# import random
# from flask import jsonify

# @api_bp.route('/metrics/<resource_id>', methods=['GET'])
# def get_metrics(resource_id):
#     try:
#         # Pour l'instant, on simule une charge CPU aléatoire
#         # En phase B réelle, on cherchera ici dans Gnocchi/Prometheus
#         mock_data = {
#             "timestamp": time.time(),
#             "cpu_util": random.uniform(15.0, 65.0),
#             "memory_util": random.uniform(30.0, 45.0),
#             "resource_id": resource_id
#         }
#         return jsonify(mock_data), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500