"""
Routes principales : pages HTML et API d'etat general.
"""

import logging
from flask import Blueprint, render_template, jsonify
from backend.config import Config
from backend.services.openstack_service import OpenStackService

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Page principale - Dashboard."""
    return render_template("index.html")


@main_bp.route("/stacks")
def stacks():
    """Page de gestion des stacks."""
    return render_template("stacks.html")


@main_bp.route("/vms")
def vms():
    """Page de gestion des VMs."""
    return render_template("vms.html")


@main_bp.route("/monitoring")
def monitoring():
    """Page de monitoring temps reel."""
    return render_template("monitoring.html")


@main_bp.route("/templates")
def templates():
    """Page de gestion des templates."""
    return render_template("templates_page.html")


@main_bp.route("/api/status", methods=["GET"])
def statut():
    """Verifie l'etat general de l'application et la connexion OpenStack."""
    try:
        connexion_ok = OpenStackService.verify_connection()
        return jsonify({
            "success": True,
            "openstack_connected": connexion_ok,
            "dashboard_ip": Config.get_dashboard_ip(),
            "dashboard_port": Config.DASHBOARD_PORT,
            "public_network": Config.PUBLIC_NETWORK_NAME,
        })
    except Exception as e:
        logger.error(f"GET /api/status : {e}")
        return jsonify({
            "success": False,
            "openstack_connected": False,
            "error": str(e)
        }), 500


@main_bp.route("/api/environment", methods=["GET"])
def environnement():
    """Retourne les informations de l'environnement detecte."""
    try:
        images = OpenStackService.get_available_images()
        flavors = OpenStackService.get_available_flavors()
        keypairs = OpenStackService.get_keypairs()

        return jsonify({
            "success": True,
            "images": images,
            "flavors": flavors,
            "keypairs": keypairs,
            "public_network": Config.PUBLIC_NETWORK_NAME,
            "default_image": Config.DEFAULT_IMAGE,
            "default_flavor": Config.DEFAULT_FLAVOR,
        })
    except Exception as e:
        logger.error(f"GET /api/environment : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
