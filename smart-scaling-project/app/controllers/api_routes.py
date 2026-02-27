# from flask import Blueprint, jsonify, request, current_app
# import time

# # On crée un Blueprint pour organiser les routes
# api_bp = Blueprint('api', __name__)

# @api_bp.route('/api/instances', methods=['GET'])
# def get_instances():
#     model = current_app.config['MODEL']
#     scaler = current_app.config['SCALER']
#     try:
#         servers = model.get_all_servers()
#         result = []
#         for s in servers:
#             # On enrichit les données comme dans ton server.py
#             cpu_avg, _ = model.get_metrics(s.id, "cpu_util")
#             result.append({
#                 "id": s.id,
#                 "name": s.name,
#                 "status": s.status,
#                 "metrics": {"cpu_percent": cpu_avg},
#                 "monitored": s.id in scaler.monitored_instances
#             })
#         return jsonify({"instances": result})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @api_bp.route('/api/scaler/start', methods=['POST'])
# def start_scaler():
#     scaler = current_app.config['SCALER']
#     data = request.json
#     instance_id = data.get('instance_id')
#     stack_name = data.get('stack_name', 'manual')
    
#     if not instance_id:
#         return jsonify({"error": "instance_id requis"}), 400
        
#     scaler.start_monitoring(instance_id, stack_name)
#     return jsonify({"status": "monitoring_started", "instance_id": instance_id})

# @api_bp.route('/api/scaler/stop', methods=['POST'])
# def stop_scaler():
#     scaler = current_app.config['SCALER']
#     instance_id = request.json.get('instance_id')
#     scaler.stop_monitoring(instance_id)
#     return jsonify({"status": "stopped"})

# @api_bp.route('/api/stacks', methods=['GET'])
# def list_stacks():
#     model = current_app.config['MODEL']
#     try:
#         stacks = model.get_stacks()
#         return jsonify([{"id": s.id, "name": s.name, "status": s.status} for s in stacks])
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500