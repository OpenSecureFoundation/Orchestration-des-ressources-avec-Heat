"""
Routes API pour la collecte et consultation des metriques.
"""

import logging
from flask import Blueprint, request, jsonify
from backend.services.metrics_service import MetricsService
from backend.services.scaling_service import ScalingService

logger = logging.getLogger(__name__)
metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/metrics")


@metrics_bp.route("/alert", methods=["POST"])
def recevoir_metriques():
    """
    Point d'entree pour les agents de metriques dans les VMs.
    Recoit les donnees JSON et les enregistre.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Donnees JSON manquantes"}), 400

        succes = MetricsService.receive_metrics(data)
        if succes:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Echec enregistrement"}), 500

    except Exception as e:
        logger.error(f"POST /api/metrics/alert : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route("/<server_id>/history", methods=["GET"])
def historique_metriques(server_id):
    """Retourne l'historique des metriques d'une VM."""
    try:
        hours = int(request.args.get("hours", 24))
        historique = MetricsService.get_metrics_history(server_id, hours)
        return jsonify({"success": True, "history": historique})
    except Exception as e:
        logger.error(f"GET /api/metrics/{server_id}/history : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route("/<server_id>/latest", methods=["GET"])
def dernieres_metriques(server_id):
    """Retourne la derniere metrique connue d'une VM."""
    try:
        metrics = MetricsService.get_latest_metrics(server_id)
        return jsonify({"success": True, "metrics": metrics})
    except Exception as e:
        logger.error(f"GET /api/metrics/{server_id}/latest : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route("/all/latest", methods=["GET"])
def toutes_dernieres_metriques():
    """Retourne la derniere metrique de chaque VM connue."""
    try:
        metrics = MetricsService.get_all_servers_latest()
        return jsonify({"success": True, "metrics": metrics})
    except Exception as e:
        logger.error(f"GET /api/metrics/all/latest : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route("/scaling/<server_id>", methods=["GET"])
def politique_scaling(server_id):
    """Retourne la politique de scaling d'une VM."""
    try:
        politique = ScalingService.get_policy(server_id)
        return jsonify({"success": True, "policy": politique})
    except Exception as e:
        logger.error(f"GET /api/metrics/scaling/{server_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route("/scaling/<server_id>", methods=["POST"])
def creer_politique_scaling(server_id):
    """Cree ou met a jour une politique de scaling."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Donnees JSON manquantes"}), 400

        politique = ScalingService.create_policy(
            server_id=server_id,
            server_name=data.get("server_name", server_id),
            metric=data.get("metric", "cpu"),
            threshold_up=float(data.get("threshold_up", 80)),
            threshold_down=float(data.get("threshold_down", 20)),
            cooldown=int(data.get("cooldown", 60)),
        )
        return jsonify({"success": True, "policy": politique}), 201

    except Exception as e:
        logger.error(f"POST /api/metrics/scaling/{server_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route("/scaling/<server_id>", methods=["DELETE"])
def supprimer_politique_scaling(server_id):
    """Supprime la politique de scaling d'une VM."""
    try:
        ScalingService.delete_policy(server_id)
        return jsonify({"success": True, "message": "Politique supprimee"})
    except Exception as e:
        logger.error(f"DELETE /api/metrics/scaling/{server_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route("/scaling", methods=["GET"])
def lister_politiques():
    """Retourne toutes les politiques de scaling."""
    try:
        politiques = ScalingService.list_all_policies()
        return jsonify({"success": True, "policies": politiques})
    except Exception as e:
        logger.error(f"GET /api/metrics/scaling : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
