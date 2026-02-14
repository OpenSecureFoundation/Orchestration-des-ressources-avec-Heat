"""
auth.py
Responsabilité : Gestion de l'authentification et des sessions.
Centralise toute la logique de sécurité d'accès au dashboard.
"""

import os
import time
import logging
import hashlib
import secrets
from functools import wraps
from flask import session, jsonify, request
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURATION DU LOGGER
# ============================================================
logger = logging.getLogger("auth")

# ============================================================
# CONFIGURATION DE SÉCURITÉ
# ============================================================
# Durée maximale d'une session en secondes (2 heures)
SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME", "7200"))

# Nombre maximum de tentatives de connexion avant blocage
MAX_TENTATIVES = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))

# Durée du blocage après trop de tentatives (en secondes)
BLOCAGE_DUREE = int(os.getenv("LOCKOUT_DURATION", "300"))

# ============================================================
# UTILISATEURS AUTORISÉS
# En production ces données viendraient d'une base de données
# ============================================================
def _hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Hash un mot de passe avec SHA-256."""
    return hashlib.sha256(mot_de_passe.encode()).hexdigest()


UTILISATEURS = {
    os.getenv("DASHBOARD_USER", "admin"): {
        "password_hash": _hasher_mot_de_passe(
            os.getenv("DASHBOARD_PASSWORD", "admin123")
        ),
        "role": "admin",
        "nom_complet": "Administrateur Cloud"
    }
}

# ============================================================
# SUIVI DES TENTATIVES DE CONNEXION
# Protège contre les attaques par force brute
# ============================================================
# Structure : { "ip_address": {"tentatives": 0, "depuis": timestamp} }
_tentatives_connexion = {}


# ============================================================
# FONCTIONS DE VÉRIFICATION
# ============================================================
def est_bloque(ip: str) -> tuple[bool, int]:
    """
    Vérifie si une IP est bloquée suite à trop de
    tentatives de connexion échouées.

    Retourne :
        (True,  secondes_restantes) → IP bloquée
        (False, 0)                  → IP libre
    """
    if ip not in _tentatives_connexion:
        return False, 0

    info = _tentatives_connexion[ip]

    if info["tentatives"] < MAX_TENTATIVES:
        return False, 0

    temps_ecoule = time.time() - info["depuis"]

    if temps_ecoule < BLOCAGE_DUREE:
        restant = int(BLOCAGE_DUREE - temps_ecoule)
        return True, restant

    # Blocage expiré → on réinitialise
    del _tentatives_connexion[ip]
    return False, 0


def enregistrer_tentative_echouee(ip: str):
    """
    Enregistre une tentative de connexion échouée
    pour une IP donnée.
    """
    if ip not in _tentatives_connexion:
        _tentatives_connexion[ip] = {
            "tentatives": 0,
            "depuis":     time.time()
        }

    _tentatives_connexion[ip]["tentatives"] += 1
    tentatives = _tentatives_connexion[ip]["tentatives"]

    logger.warning(
        f"Tentative échouée depuis {ip} "
        f"({tentatives}/{MAX_TENTATIVES})"
    )

    if tentatives >= MAX_TENTATIVES:
        logger.warning(
            f"IP bloquée : {ip} pour {BLOCAGE_DUREE}s "
            f"(trop de tentatives)"
        )


def reinitialiser_tentatives(ip: str):
    """Réinitialise les tentatives après une connexion réussie."""
    if ip in _tentatives_connexion:
        del _tentatives_connexion[ip]


# ============================================================
# FONCTION PRINCIPALE DE CONNEXION
# ============================================================
def connecter_utilisateur(username: str, password: str, ip: str) -> dict:
    """
    Vérifie les identifiants et connecte l'utilisateur.

    Paramètres :
        username (str) : Nom d'utilisateur
        password (str) : Mot de passe en clair
        ip       (str) : IP du client (pour anti-brute force)

    Retourne un dict avec :
        success  (bool)  : True si connexion réussie
        message  (str)   : Description du résultat
        role     (str)   : Rôle de l'utilisateur (si succès)
        bloque   (bool)  : True si IP bloquée
        restant  (int)   : Secondes avant déblocage
    """

    # --- Vérification du blocage IP ---
    bloque, restant = est_bloque(ip)
    if bloque:
        logger.warning(f"Connexion bloquée pour IP : {ip}")
        return {
            "success": False,
            "message": f"Trop de tentatives. Réessayez dans {restant}s",
            "bloque":  True,
            "restant": restant
        }

    # --- Vérification username ---
    if username not in UTILISATEURS:
        enregistrer_tentative_echouee(ip)
        logger.warning(f"Utilisateur inconnu : '{username}' depuis {ip}")
        return {
            "success": False,
            "message": "Identifiants incorrects",
            "bloque":  False,
            "restant": 0
        }

    # --- Vérification mot de passe ---
    hash_fourni  = _hasher_mot_de_passe(password)
    hash_stocke  = UTILISATEURS[username]["password_hash"]

    if not secrets.compare_digest(hash_fourni, hash_stocke):
        enregistrer_tentative_echouee(ip)
        return {
            "success": False,
            "message": "Identifiants incorrects",
            "bloque":  False,
            "restant": 0
        }

    # --- Connexion réussie ---
    reinitialiser_tentatives(ip)
    role = UTILISATEURS[username]["role"]

    logger.info(f"Connexion réussie : {username} ({role}) depuis {ip}")

    return {
        "success":    True,
        "message":    "Connexion réussie",
        "username":   username,
        "role":       role,
        "nom_complet": UTILISATEURS[username]["nom_complet"],
        "bloque":     False,
        "restant":    0
    }


# ============================================================
# GESTION DE LA SESSION
# ============================================================
def creer_session(username: str, role: str, nom_complet: str):
    """
    Crée une session sécurisée après connexion réussie.
    Stocke les infos dans la session Flask.
    """
    session.permanent = True
    session["user"]         = username
    session["role"]         = role
    session["nom_complet"]  = nom_complet
    session["login_time"]   = time.time()
    session["session_id"]   = secrets.token_hex(16)

    logger.info(f"Session créée pour : {username}")


def detruire_session():
    """Détruit la session active."""
    user = session.get("user", "inconnu")
    session.clear()
    logger.info(f"Session détruite pour : {user}")


def session_valide() -> bool:
    """
    Vérifie que la session est valide et non expirée.

    Retourne :
        True  → session valide
        False → session absente ou expirée
    """
    if "user" not in session:
        return False

    # Vérification de l'expiration
    login_time = session.get("login_time", 0)
    if time.time() - login_time > SESSION_LIFETIME:
        logger.info(
            f"Session expirée pour : {session.get('user')}"
        )
        detruire_session()
        return False

    return True


def get_utilisateur_courant() -> dict | None:
    """
    Retourne les infos de l'utilisateur connecté.
    Retourne None si pas de session valide.
    """
    if not session_valide():
        return None

    return {
        "username":   session.get("user"),
        "role":       session.get("role"),
        "nom_complet": session.get("nom_complet"),
        "login_time": session.get("login_time"),
    }


# ============================================================
# DÉCORATEUR DE PROTECTION DES ROUTES
# ============================================================
def login_requis(f):
    """
    Décorateur à placer sur les routes protégées.
    Redirige vers la page de connexion si non authentifié.

    Utilisation :
        @app.route("/dashboard")
        @login_requis
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session_valide():
            # Requête API → retourne JSON
            if request.path.startswith("/api/"):
                return jsonify({
                    "error":   "Non autorisé",
                    "message": "Session expirée ou invalide"
                }), 401

            # Page web → redirige vers login
            from flask import redirect, url_for
            return redirect(url_for("index"))

        return f(*args, **kwargs)
    return decorated


def admin_requis(f):
    """
    Décorateur pour les routes réservées aux administrateurs.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session_valide():
            return jsonify({"error": "Non autorisé"}), 401

        if session.get("role") != "admin":
            logger.warning(
                f"Accès refusé (rôle insuffisant) pour "
                f"{session.get('user')} sur {request.path}"
            )
            return jsonify({
                "error": "Accès refusé",
                "message": "Droits administrateur requis"
            }), 403

        return f(*args, **kwargs)
    return decorated


# ============================================================
# INFORMATIONS DE SÉCURITÉ
# ============================================================
def get_info_securite() -> dict:
    """
    Retourne les informations de sécurité actuelles.
    Utile pour le monitoring et le débogage.
    """
    return {
        "session_lifetime_secondes": SESSION_LIFETIME,
        "max_tentatives":            MAX_TENTATIVES,
        "duree_blocage_secondes":    BLOCAGE_DUREE,
        "ips_bloquees":              len([
            ip for ip in _tentatives_connexion
            if _tentatives_connexion[ip]["tentatives"] >= MAX_TENTATIVES
        ]),
        "utilisateurs_configures": list(UTILISATEURS.keys())
    }