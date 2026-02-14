"""
routes.py
Responsabilité : Centralise tous les endpoints REST
de l'application. Ces routes sont appelées par le
frontend JavaScript via fetch().

Organisation des routes :
    /api/metrics      → Métriques VM
    /api/policies     → Politiques de scaling
    /api/templates    → Gestion des templates
    /api/stack        → Statut de la stack Heat
    /api/logs         → Journal des actions
    /api/stats        → Statistiques générales
    /api/auth         → Informations de session
"""

import os
import time
import logging
from flask import Blueprint, jsonify, request, session
from api.auth import login_requis, admin_requis, get_utilisateur_courant

# ============================================================
# CONFIGURATION DU LOGGER
# ============================================================
logger = logging.getLogger("routes")

# ============================================================
# BLUEPRINT FLASK
# Un Blueprint regroupe des routes dans un module séparé.
# Il sera enregistré dans adapter.py avec :
# app.register_blueprint(api_bp, url_prefix="/api")
# ============================================================
api_bp = Blueprint("api", __name__)

# Référence vers le state global (injecté depuis adapter.py)
_state_ref = None


def initialiser(state: dict):
    """
    Initialise le module routes avec le state global.
    Appelé une seule fois au démarrage depuis adapter.py.
    """
    global _state_ref
    _state_ref = state
    logger.info("Module routes initialisé")


# ============================================================
# HELPER — Réponse d'erreur standardisée
# ============================================================
def erreur(message: str, code: int = 400) -> tuple:
    """Retourne une réponse d'erreur JSON standardisée."""
    return jsonify({
        "success": False,
        "error":   message,
        "time":    time.strftime("%H:%M:%S")
    }), code


def succes(data: dict = None, message: str = "OK") -> tuple:
    """Retourne une réponse de succès JSON standardisée."""
    response = {
        "success": True,
        "message": message,
        "time":    time.strftime("%H:%M:%S")
    }
    if data:
        response.update(data)
    return jsonify(response), 200


# ============================================================
# ROUTES — MÉTRIQUES
# ============================================================
@api_bp.route("/metrics", methods=["GET"])
@login_requis
def get_metrics():
    """
    Retourne les métriques actuelles de la VM.

    Réponse :
    {
        "cpu":     72.5,
        "ram":     45.2,
        "flavor":  "m1.medium",
        "status":  "ACTIVE",
        "timestamp": 1700000000.0
    }
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    vm = _state_ref["vm"]

    return jsonify({
        "success":      True,
        "cpu":          round(vm.get("cpu",  0), 1),
        "ram":          round(vm.get("ram",  0), 1),
        "flavor":       vm.get("current_flavor", "m1.small"),
        "status":       vm.get("status", "UNKNOWN"),
        "vm_name":      vm.get("name", ""),
        "private_ip":   vm.get("private_ip", ""),
        "public_ip":    vm.get("public_ip", ""),
        "last_update":  vm.get("last_update", "--:--"),
        "timestamp":    time.time()
    })


@api_bp.route("/metrics/history", methods=["GET"])
@login_requis
def get_metrics_history():
    """
    Retourne l'historique des métriques.
    Le frontend utilise ces données pour construire
    les graphiques au premier chargement.
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    historique = _state_ref.get("metrics_history", [])

    return jsonify({
        "success":    True,
        "historique": historique,
        "count":      len(historique)
    })


# ============================================================
# ROUTES — POLITIQUES DE SCALING
# ============================================================
@api_bp.route("/policies", methods=["GET"])
@login_requis
def get_policies():
    """
    Retourne les politiques de scaling actuelles.

    Réponse :
    {
        "scale_up_threshold":   80,
        "scale_down_threshold": 20,
        "cooldown":             120,
        "evaluation_periods":   3,
        "period_seconds":       60
    }
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    return jsonify({
        "success":  True,
        "policies": _state_ref["policies"]
    })


@api_bp.route("/policies", methods=["PUT"])
@admin_requis
def update_policies():
    """
    Met à jour les politiques de scaling.
    Réservé aux administrateurs (@admin_requis).

    Corps attendu (JSON) :
    {
        "scale_up_threshold":   85,
        "scale_down_threshold": 15
    }
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    data = request.get_json()

    if not data:
        return erreur("Corps de requête manquant")

    scale_up   = data.get("scale_up_threshold")
    scale_down = data.get("scale_down_threshold")

    # --- Validation ---
    if scale_up is None or scale_down is None:
        return erreur("Paramètres manquants : scale_up_threshold et scale_down_threshold requis")

    if not isinstance(scale_up, (int, float)) or \
       not isinstance(scale_down, (int, float)):
        return erreur("Les seuils doivent être des nombres")

    if not (0 < scale_down < scale_up < 100):
        return erreur(
            "Seuils invalides : "
            "0 < scale_down < scale_up < 100"
        )

    # --- Mise à jour ---
    anciennes = dict(_state_ref["policies"])
    _state_ref["policies"]["scale_up_threshold"]   = int(scale_up)
    _state_ref["policies"]["scale_down_threshold"] = int(scale_down)

    user = get_utilisateur_courant()
    logger.info(
        f"Politiques mises à jour par {user['username']} : "
        f"Scale Up={scale_up}% | Scale Down={scale_down}%"
    )

    # Ajout dans les logs applicatifs
    _state_ref["logs"].insert(0, {
        "time":    time.strftime("%H:%M"),
        "type":    "info",
        "message": (
            f"Politiques mises à jour par {user['username']} : "
            f"Scale Up={scale_up}% | Scale Down={scale_down}%"
        )
    })

    return succes(
        data={"policies": _state_ref["policies"]},
        message="Politiques mises à jour avec succès"
    )


@api_bp.route("/policies/reset", methods=["POST"])
@admin_requis
def reset_policies():
    """
    Remet les politiques aux valeurs par défaut.
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    _state_ref["policies"]["scale_up_threshold"]   = 80
    _state_ref["policies"]["scale_down_threshold"] = 20
    _state_ref["policies"]["cooldown"]             = 120
    _state_ref["policies"]["evaluation_periods"]   = 3
    _state_ref["policies"]["period_seconds"]       = 60

    logger.info("Politiques réinitialisées aux valeurs par défaut")

    return succes(
        data={"policies": _state_ref["policies"]},
        message="Politiques réinitialisées"
    )


# ============================================================
# ROUTES — TEMPLATES
# ============================================================
@api_bp.route("/templates", methods=["GET"])
@login_requis
def get_templates():
    """
    Retourne la liste des templates Heat disponibles.
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    return jsonify({
        "success":   True,
        "templates": _state_ref["templates"],
        "count":     len(_state_ref["templates"])
    })


@api_bp.route("/deploy", methods=["POST"])
@admin_requis
def deploy_template():
    """
    Déploie un template Heat sélectionné.

    Corps attendu (JSON) :
    {
        "template": "main_stack.yaml"
    }
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    data          = request.get_json()
    template_name = data.get("template") if data else None

    if not template_name:
        return erreur("Nom du template manquant")

    # Vérifier que le template existe dans la liste
    templates_noms = [t["name"] for t in _state_ref["templates"]]
    if template_name not in templates_noms:
        return erreur(f"Template inconnu : {template_name}")

    user = get_utilisateur_courant()

    logger.info(
        f"Déploiement de '{template_name}' "
        f"par {user['username']}"
    )

    # Ajout dans les logs
    _state_ref["logs"].insert(0, {
        "time":    time.strftime("%H:%M"),
        "type":    "success",
        "message": (
            f"Déploiement '{template_name}' "
            f"lancé par {user['username']}"
        )
    })

    return succes(
        message=f"Template '{template_name}' déployé avec succès"
    )


# ============================================================
# ROUTES — STACK HEAT
# ============================================================
@api_bp.route("/stack/status", methods=["GET"])
@login_requis
def get_stack_status():
    """
    Retourne le statut complet de la stack Heat
    et de toute l'infrastructure.
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    try:
        import heat_client
        statut_openstack = heat_client.get_statut_stack()
    except Exception:
        statut_openstack = {
            "status":  "SIMULATION",
            "message": "OpenStack non disponible"
        }

    return jsonify({
        "success":    True,
        "stack":      statut_openstack,
        "vm":         _state_ref["vm"],
        "flavors":    _state_ref["flavors"],
        "policies":   _state_ref["policies"],
        "stats":      _state_ref["stats"],
    })


@api_bp.route("/stack/flavors", methods=["GET"])
@login_requis
def get_flavors():
    """
    Retourne la liste des flavors disponibles
    et leurs caractéristiques.
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    flavors = _state_ref["flavors"]
    current = _state_ref["vm"]["current_flavor"]

    # Enrichit chaque flavor avec son statut actif
    flavors_enrichis = {}
    for nom, specs in flavors.items():
        flavors_enrichis[nom] = {
            **specs,
            "actif": nom == current
        }

    return jsonify({
        "success":         True,
        "flavors":         flavors_enrichis,
        "current_flavor":  current
    })


# ============================================================
# ROUTES — JOURNAL
# ============================================================
@api_bp.route("/logs", methods=["GET"])
@login_requis
def get_logs():
    """
    Retourne le journal des actions.
    Paramètre optionnel : ?limit=20 (défaut: 20, max: 50)
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    limit = min(int(request.args.get("limit", 20)), 50)
    logs  = _state_ref["logs"][:limit]

    return jsonify({
        "success": True,
        "logs":    logs,
        "count":   len(logs),
        "total":   len(_state_ref["logs"])
    })


@api_bp.route("/logs/clear", methods=["DELETE"])
@admin_requis
def clear_logs():
    """Efface le journal des actions."""
    if not _state_ref:
        return erreur("State non initialisé", 500)

    _state_ref["logs"] = [{
        "time":    time.strftime("%H:%M"),
        "type":    "info",
        "message": "Journal effacé par l'administrateur"
    }]

    return succes(message="Journal effacé")


# ============================================================
# ROUTES — STATISTIQUES
# ============================================================
@api_bp.route("/stats", methods=["GET"])
@login_requis
def get_stats():
    """
    Retourne les statistiques de l'adaptateur.

    Réponse :
    {
        "alertes_recues":   150,
        "alertes_valides":  145,
        "alertes_rejetees": 5,
        "scalings_up":      3,
        "scalings_down":    1
    }
    """
    if not _state_ref:
        return erreur("State non initialisé", 500)

    stats = _state_ref["stats"]

    # Calcul du taux de validation
    recues = stats.get("alertes_recues", 0)
    taux   = (
        round(stats.get("alertes_valides", 0) / recues * 100, 1)
        if recues > 0 else 0
    )

    return jsonify({
        "success":           True,
        "stats":             stats,
        "taux_validation":   taux,
        "total_scalings":    (
            stats.get("scalings_up", 0) +
            stats.get("scalings_down", 0)
        )
    })


# ============================================================
# ROUTES — AUTHENTIFICATION
# ============================================================
@api_bp.route("/auth/me", methods=["GET"])
@login_requis
def get_current_user():
    """
    Retourne les infos de l'utilisateur connecté.
    Utilisé par le frontend pour afficher le nom d'utilisateur.
    """
    user = get_utilisateur_courant()
    if not user:
        return erreur("Session invalide", 401)

    return jsonify({
        "success":    True,
        "username":   user["username"],
        "role":       user["role"],
        "nom_complet": user["nom_complet"],
    })


@api_bp.route("/auth/status", methods=["GET"])
def get_auth_status():
    """
    Vérifie si l'utilisateur est connecté.
    Ne nécessite pas @login_requis car
    c'est justement pour vérifier l'état.
    """
    from api.auth import session_valide
    connecte = session_valide()

    return jsonify({
        "success":   True,
        "connecte":  connecte,
        "username":  session.get("user") if connecte else None,
        "role":      session.get("role") if connecte else None,
    })