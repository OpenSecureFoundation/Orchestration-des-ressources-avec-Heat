"""
Routes API pour la gestion des VMs Nova.
"""
import logging
from flask import Blueprint, request, jsonify
from backend.services.vm_service import VMService
from backend.services.openstack_service import OpenStackService
from backend.services.scaling_service import ScalingService

logger = logging.getLogger(__name__)
vm_bp = Blueprint("vms", __name__, url_prefix="/api/vms")


@vm_bp.route("", methods=["GET"])
def lister_vms():
    try:
        vms = VMService.list_all_vms()
        return jsonify({"success": True, "vms": vms})
    except Exception as e:
        logger.error(f"GET /api/vms : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>", methods=["GET"])
def details_vm(vm_id):
    try:
        vm = VMService.get_vm_details(vm_id)
        return jsonify({"success": True, "vm": vm})
    except Exception as e:
        logger.error(f"GET /api/vms/{vm_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>/resize", methods=["POST"])
def resize_vm(vm_id):
    try:
        data = request.get_json()
        if not data or not data.get("flavor"):
            return jsonify({"success": False, "error": "Le champ 'flavor' est obligatoire"}), 400
        VMService.resize_vm(vm_id, data["flavor"])
        return jsonify({"success": True, "message": f"Resize lance vers {data['flavor']}"})
    except Exception as e:
        logger.error(f"POST /api/vms/{vm_id}/resize : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>/start", methods=["POST"])
def demarrer_vm(vm_id):
    try:
        nc = OpenStackService.get_nova_client()
        server = nc.servers.get(vm_id)
        server.start()
        logger.info(f"VM '{vm_id}' demarree")
        return jsonify({"success": True, "message": "VM en cours de demarrage"})
    except Exception as e:
        logger.error(f"POST /api/vms/{vm_id}/start : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>/stop", methods=["POST"])
def arreter_vm(vm_id):
    try:
        nc = OpenStackService.get_nova_client()
        server = nc.servers.get(vm_id)
        server.stop()
        logger.info(f"VM '{vm_id}' arretee")
        return jsonify({"success": True, "message": "VM en cours d'arret"})
    except Exception as e:
        logger.error(f"POST /api/vms/{vm_id}/stop : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>/console", methods=["GET"])
def console_vm(vm_id):
    try:
        log = VMService.get_console_log(vm_id)
        return jsonify({"success": True, "log": log})
    except Exception as e:
        logger.error(f"GET /api/vms/{vm_id}/console : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>/metrics", methods=["GET"])
def metriques_vm(vm_id):
    try:
        metrics = VMService.get_vm_metrics(vm_id)
        return jsonify({"success": True, "metrics": metrics})
    except Exception as e:
        logger.error(f"GET /api/vms/{vm_id}/metrics : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>/scaling-history", methods=["GET"])
def historique_scaling(vm_id):
    try:
        hist = ScalingService.get_history(vm_id)
        return jsonify({"success": True, "history": hist})
    except Exception as e:
        logger.error(f"GET /api/vms/{vm_id}/scaling-history : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/flavors", methods=["GET"])
def lister_flavors():
    try:
        flavors = OpenStackService.get_available_flavors()
        return jsonify({"success": True, "flavors": flavors})
    except Exception as e:
        logger.error(f"GET /api/vms/flavors : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@vm_bp.route("/<vm_id>", methods=["DELETE"])
def supprimer_vm(vm_id):
    try:
        nc = OpenStackService.get_nova_client()
        server = nc.servers.get(vm_id)
        server.delete()
        logger.info(f"VM '{vm_id}' supprimee")
        return jsonify({"success": True, "message": "VM supprimee"})
    except Exception as e:
        logger.error(f"DELETE /api/vms/{vm_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
