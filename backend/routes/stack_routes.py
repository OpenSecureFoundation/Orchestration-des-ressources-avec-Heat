"""
Routes API pour la gestion des stacks Heat.
"""

import logging
from flask import Blueprint, request, jsonify
from backend.services.stack_service import StackService

logger = logging.getLogger(__name__)
stack_bp = Blueprint("stacks", __name__, url_prefix="/api/stacks")


@stack_bp.route("", methods=["GET"])
def lister_stacks():
    """Retourne la liste de toutes les stacks."""
    try:
        stacks = StackService.list_all_stacks()
        return jsonify({"success": True, "stacks": stacks})
    except Exception as e:
        logger.error(f"GET /api/stacks : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stack_bp.route("", methods=["POST"])
def creer_stack():
    """Cree une nouvelle stack Heat."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Donnees JSON manquantes"}), 400

        name = data.get("name")
        template_id = data.get("template_id")
        parameters = data.get("parameters", {})

        if not name or not template_id:
            return jsonify({
                "success": False,
                "error": "Les champs 'name' et 'template_id' sont obligatoires"
            }), 400

        stack = StackService.create_stack(name, template_id, parameters)
        return jsonify({"success": True, "stack": stack}), 201

    except Exception as e:
        logger.error(f"POST /api/stacks : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stack_bp.route("/<stack_id>", methods=["GET"])
def statut_stack(stack_id):
    """Retourne le statut d'une stack."""
    try:
        status = StackService.get_stack_status(stack_id)
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logger.error(f"GET /api/stacks/{stack_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stack_bp.route("/<stack_id>", methods=["DELETE"])
def supprimer_stack(stack_id):
    """Supprime une stack."""
    try:
        StackService.delete_stack(stack_id)
        return jsonify({"success": True, "message": "Stack supprimee"})
    except Exception as e:
        logger.error(f"DELETE /api/stacks/{stack_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stack_bp.route("/<stack_id>/resources", methods=["GET"])
def ressources_stack(stack_id):
    """Retourne les ressources d'une stack."""
    try:
        ressources = StackService.get_stack_resources(stack_id)
        return jsonify({"success": True, "resources": ressources})
    except Exception as e:
        logger.error(f"GET /api/stacks/{stack_id}/resources : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stack_bp.route("/<stack_id>/outputs", methods=["GET"])
def outputs_stack(stack_id):
    """Retourne les outputs d'une stack."""
    try:
        outputs = StackService.get_stack_outputs(stack_id)
        return jsonify({"success": True, "outputs": outputs})
    except Exception as e:
        logger.error(f"GET /api/stacks/{stack_id}/outputs : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stack_bp.route("/<stack_id>/events", methods=["GET"])
def evenements_stack(stack_id):
    """Retourne les evenements d'une stack."""
    try:
        evenements = StackService.get_stack_events(stack_id)
        return jsonify({"success": True, "events": evenements})
    except Exception as e:
        logger.error(f"GET /api/stacks/{stack_id}/events : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
