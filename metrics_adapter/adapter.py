"""
adapter.py
Responsabilité : Chef d'orchestre du système de scaling.

Il fait 3 choses en parallèle :
1. Reçoit les alertes des VMs  → les valide → décide du scaling
2. Sert l'API REST             → le frontend lit/modifie les données
3. Émet les métriques          → WebSocket temps réel vers le dashboard
"""

import os
import time
import threading
import logging
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Import de nos modules
from validator import valider_alerte, determiner_action, determiner_nouveau_flavor
import heat_client

load_dotenv()

# ============================================================
# CONFIGURATION LOGGER
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("adapter")

# ============================================================
# INITIALISATION FLASK
# ============================================================
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../frontend"),
    static_folder=os.path.join(os.path.dirname(__file__), "../frontend/static")
)
app.secret_key = os.getenv("SECRET_KEY", "heat-dashboard-secret-2024")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ============================================================
# IDENTIFIANTS DU DASHBOARD
# ============================================================
DASHBOARD_USER     = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")
VM_NAME            = os.getenv("VM_NAME", "heat-vm-01")

# ============================================================
# ÉTAT GLOBAL DE L'APPLICATION
# Toutes les données partagées entre les threads et le frontend
# ============================================================
state = {
    # --- Métriques VM ---
    "vm": {
        "name":           VM_NAME,
        "status":         "ACTIVE",
        "private_ip":     os.getenv("VM_PRIVATE_IP", "192.168.1.10"),
        "public_ip":      os.getenv("VM_PUBLIC_IP", "10.0.0.100"),
        "current_flavor": "m1.small",
        "cpu":            0.0,
        "ram":            0.0,
        "last_update":    None,
    },

    # --- Politiques de scaling ---
    "policies": {
        "scale_up_threshold":   int(os.getenv("SCALE_UP_THRESHOLD",   "80")),
        "scale_down_threshold": int(os.getenv("SCALE_DOWN_THRESHOLD", "20")),
        "cooldown":             int(os.getenv("COOLDOWN_SECONDS",      "120")),
        "evaluation_periods":   3,
        "period_seconds":       60,
    },

    # --- Flavors disponibles ---
    "flavors": {
        "m1.small":  {"cpu": 1, "ram": "2 GB",  "disk": "20 GB"},
        "m1.medium": {"cpu": 2, "ram": "4 GB",  "disk": "40 GB"},
        "m1.large":  {"cpu": 4, "ram": "8 GB",  "disk": "80 GB"},
    },

    # --- Templates disponibles ---
    "templates": [
        {
            "name": "main_stack.yaml",
            "description": "Template racine — déploie toute l'infrastructure"
        },
        {
            "name": "network_template.yaml",
            "description": "Réseau privé, sous-réseau, routeur et sécurité"
        },
        {
            "name": "vm_template.yaml",
            "description": "Machine virtuelle avec agent métriques"
        },
        {
            "name": "autoscaling_template.yaml",
            "description": "Politiques de scaling vertical"
        },
    ],

    # --- Journal des actions ---
    "logs": [
        {
            "time":    time.strftime("%H:%M"),
            "type":    "info",
            "message": "Adaptateur de métriques démarré"
        }
    ],

    # --- Statistiques ---
    "stats": {
        "alertes_recues":   0,
        "alertes_valides":  0,
        "alertes_rejetees": 0,
        "scalings_up":      0,
        "scalings_down":    0,
    }
}

# Verrou pour éviter les conflits entre threads
state_lock = threading.Lock()


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================
def ajouter_log(message: str, type_log: str = "info"):
    """Ajoute une entrée dans le journal et garde les 50 dernières."""
    with state_lock:
        state["logs"].insert(0, {
            "time":    time.strftime("%H:%M"),
            "type":    type_log,
            "message": message
        })
        # On garde seulement les 50 dernières entrées
        if len(state["logs"]) > 50:
            state["logs"] = state["logs"][:50]


def emettre_metriques():
    """
    Émet les métriques actuelles vers tous les clients
    connectés au dashboard via WebSocket.
    """
    socketio.emit("metrics_update", {
        "cpu":    round(state["vm"]["cpu"], 1),
        "ram":    round(state["vm"]["ram"], 1),
        "flavor": state["vm"]["current_flavor"],
        "status": state["vm"]["status"],
        "logs":   state["logs"][:10],
        "stats":  state["stats"],
    })


# ============================================================
# ROUTE PRINCIPALE — RÉCEPTION DES ALERTES DES VMs
# ============================================================
@app.route("/alert", methods=["POST"])
def recevoir_alerte():
    """
    Endpoint appelé par l'agent tournant sur chaque VM.
    Reçoit les métriques, les valide et décide du scaling.

    Corps attendu (JSON) :
    {
        "source":    "heat-vm-01",
        "token":     "heat-secret-token",
        "cpu":       85.2,
        "ram":       60.1,
        "timestamp": 1700000000.0
    }
    """
    with state_lock:
        state["stats"]["alertes_recues"] += 1

    data = request.get_json()
    logger.info(f"Alerte reçue de : {data.get('source', 'inconnu')}")

    # --- ÉTAPE 1 : Validation ---
    valide, raison = valider_alerte(data)

    if not valide:
        with state_lock:
            state["stats"]["alertes_rejetees"] += 1
        ajouter_log(f"Alerte rejetée : {raison}", "warning")
        logger.warning(f"Alerte rejetée : {raison}")
        return jsonify({"success": False, "reason": raison}), 400

    with state_lock:
        state["stats"]["alertes_valides"] += 1

    # --- ÉTAPE 2 : Mise à jour des métriques ---
    with state_lock:
        state["vm"]["cpu"]         = data["cpu"]
        state["vm"]["ram"]         = data["ram"]
        state["vm"]["last_update"] = time.strftime("%H:%M:%S")

    # --- ÉTAPE 3 : Décision de scaling ---
    action = determiner_action(data["cpu"], state["policies"])

    if action != "none":
        flavor_actuel  = state["vm"]["current_flavor"]
        nouveau_flavor = determiner_nouveau_flavor(action, flavor_actuel)

        # --- ÉTAPE 4 : Exécution du resize ---
        resultat = heat_client.effectuer_resize(VM_NAME, nouveau_flavor)

        if resultat["success"] and resultat["action"] not in ("none", "cooldown"):
            with state_lock:
                state["vm"]["current_flavor"] = nouveau_flavor
                if action == "scale_up":
                    state["stats"]["scalings_up"] += 1
                else:
                    state["stats"]["scalings_down"] += 1

            type_log = "success" if action == "scale_up" else "warning"
            ajouter_log(
                f"Scale {'Up' if action == 'scale_up' else 'Down'} : "
                f"{flavor_actuel} → {nouveau_flavor} "
                f"(CPU: {data['cpu']:.0f}%)",
                type_log
            )
        elif resultat["action"] == "cooldown":
            ajouter_log(f"Cooldown actif — scaling reporté", "info")
        else:
            ajouter_log(f"Erreur scaling : {resultat['message']}", "error")
    else:
        ajouter_log(
            f"Métriques reçues — CPU: {data['cpu']:.0f}% | "
            f"RAM: {data['ram']:.0f}% | Aucune action",
            "info"
        )

    # --- ÉTAPE 5 : Émission WebSocket ---
    emettre_metriques()

    return jsonify({
        "success": True,
        "action":  action,
        "flavor":  state["vm"]["current_flavor"]
    })


# ============================================================
# ROUTES — PAGES WEB
# ============================================================
@app.route("/")
def index():
    """Page de connexion."""
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    """Traitement de la connexion."""
    username = request.form.get("username")
    password = request.form.get("password")

    if username == DASHBOARD_USER and password == DASHBOARD_PASSWORD:
        session["user"] = username
        ajouter_log(f"Connexion de l'utilisateur : {username}", "info")
        return redirect(url_for("dashboard"))

    logger.warning(f"Tentative de connexion échouée pour : {username}")
    return render_template("index.html", error="Identifiants incorrects")


@app.route("/logout")
def logout():
    """Déconnexion."""
    user = session.pop("user", None)
    if user:
        ajouter_log(f"Déconnexion de : {user}", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    """Tableau de bord principal."""
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html",
                           user=session["user"],
                           state=state)


# ============================================================
# ROUTES — API REST (appelées par le frontend JavaScript)
# ============================================================
def verifier_session():
    """Vérifie que l'utilisateur est connecté."""
    if "user" not in session:
        return jsonify({"error": "Non autorisé"}), 401
    return None


@app.route("/api/metrics")
def api_metrics():
    """Retourne les métriques actuelles."""
    erreur = verifier_session()
    if erreur:
        return erreur
    return jsonify({
        "cpu":       round(state["vm"]["cpu"], 1),
        "ram":       round(state["vm"]["ram"], 1),
        "flavor":    state["vm"]["current_flavor"],
        "status":    state["vm"]["status"],
        "timestamp": time.time()
    })


@app.route("/api/policies", methods=["GET"])
def api_get_policies():
    """Retourne les politiques de scaling actuelles."""
    erreur = verifier_session()
    if erreur:
        return erreur
    return jsonify(state["policies"])


@app.route("/api/policies", methods=["PUT"])
def api_update_policies():
    """Met à jour les politiques de scaling depuis le dashboard."""
    erreur = verifier_session()
    if erreur:
        return erreur

    data = request.get_json()
    scale_up   = data.get("scale_up_threshold")
    scale_down = data.get("scale_down_threshold")

    # Validation
    if scale_up is None or scale_down is None:
        return jsonify({"error": "Paramètres manquants"}), 400

    if not (0 < scale_down < scale_up < 100):
        return jsonify({
            "error": "Seuils invalides : 0 < scale_down < scale_up < 100"
        }), 400

    # Mise à jour
    with state_lock:
        state["policies"]["scale_up_threshold"]   = scale_up
        state["policies"]["scale_down_threshold"] = scale_down

    ajouter_log(
        f"Politiques mises à jour par {session['user']} : "
        f"Scale Up={scale_up}% | Scale Down={scale_down}%",
        "info"
    )

    return jsonify({
        "success":  True,
        "message":  "Politiques mises à jour avec succès",
        "policies": state["policies"]
    })


@app.route("/api/templates")
def api_templates():
    """Retourne la liste des templates disponibles."""
    erreur = verifier_session()
    if erreur:
        return erreur
    return jsonify(state["templates"])


@app.route("/api/deploy", methods=["POST"])
def api_deploy():
    """Simule le déploiement d'un template."""
    erreur = verifier_session()
    if erreur:
        return erreur

    data          = request.get_json()
    template_name = data.get("template")

    if not template_name:
        return jsonify({"error": "Nom du template manquant"}), 400

    ajouter_log(
        f"Déploiement du template '{template_name}' "
        f"par {session['user']}",
        "success"
    )

    return jsonify({
        "success": True,
        "message": f"Template {template_name} déployé avec succès"
    })


@app.route("/api/logs")
def api_logs():
    """Retourne le journal des actions."""
    erreur = verifier_session()
    if erreur:
        return erreur
    return jsonify(state["logs"])


@app.route("/api/stack/status")
def api_stack_status():
    """Retourne le statut complet de la stack."""
    erreur = verifier_session()
    if erreur:
        return erreur
    statut = heat_client.get_statut_stack()
    return jsonify({
        **statut,
        "vm":      state["vm"],
        "stats":   state["stats"],
        "flavors": state["flavors"],
    })


@app.route("/api/stats")
def api_stats():
    """Retourne les statistiques de l'adaptateur."""
    erreur = verifier_session()
    if erreur:
        return erreur
    return jsonify(state["stats"])


# ============================================================
# WEBSOCKET — Connexion du dashboard
# ============================================================
@socketio.on("connect")
def on_connect():
    """Quand un client ouvre le dashboard."""
    logger.info("Client WebSocket connecté")
    emit("metrics_update", {
        "cpu":    round(state["vm"]["cpu"], 1),
        "ram":    round(state["vm"]["ram"], 1),
        "flavor": state["vm"]["current_flavor"],
        "status": state["vm"]["status"],
        "logs":   state["logs"][:10],
        "stats":  state["stats"],
    })


@socketio.on("disconnect")
def on_disconnect():
    """Quand un client ferme le dashboard."""
    logger.info("Client WebSocket déconnecté")


# ============================================================
# LANCEMENT DE L'APPLICATION
# ============================================================
if __name__ == "__main__":

    # Tentative de connexion à OpenStack au démarrage
    logger.info("Tentative de connexion à OpenStack...")
    connecte = heat_client.connecter()

    if connecte:
        ajouter_log("Connexion OpenStack établie", "success")
    else:
        ajouter_log("Mode simulation activé (OpenStack indisponible)", "warning")

    print("=" * 55)
    print("   Heat Orchestration — Adaptateur + Dashboard")
    print("   Dashboard : http://localhost:5000")
    print(f"   User      : {DASHBOARD_USER}")
    print(f"   Password  : {DASHBOARD_PASSWORD}")
    print(f"   OpenStack : {'✅ Connecté' if connecte else '⚠️  Mode simulation'}")
    print("=" * 55)

    socketio.run(
        app,
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )