"""
Routes API pour la gestion des templates Heat.
"""
import logging
import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from backend.config import Config
from backend.models.database import db
from backend.models.template import Template

logger = logging.getLogger(__name__)
template_bp = Blueprint("templates", __name__, url_prefix="/api/templates")


@template_bp.route("", methods=["GET"])
def lister_templates():
    try:
        templates = Template.query.all()
        return jsonify({"success": True, "templates": [t.to_dict() for t in templates]})
    except Exception as e:
        logger.error(f"GET /api/templates : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@template_bp.route("/<int:template_id>", methods=["GET"])
def detail_template(template_id):
    try:
        template = Template.query.get_or_404(template_id)
        data = template.to_dict()
        if os.path.exists(template.file_path):
            with open(template.file_path, "r") as f:
                data["content"] = f.read()
        else:
            data["content"] = ""
        return jsonify({"success": True, "template": data})
    except Exception as e:
        logger.error(f"GET /api/templates/{template_id} : {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@template_bp.route("", methods=["POST"])
def creer_ou_uploader_template():
    """
    Accepte soit un upload de fichier YAML soit un contenu texte direct
    (creation depuis l'editeur en ligne).
    """
    try:
        # Cas 1 : upload fichier
        if "file" in request.files:
            fichier = request.files["file"]
            if not fichier.filename:
                return jsonify({"success": False, "error": "Nom de fichier invalide"}), 400
            nom_fichier = secure_filename(fichier.filename)
            if not (nom_fichier.endswith(".yaml") or nom_fichier.endswith(".yml")):
                return jsonify({"success": False, "error": "Seuls .yaml et .yml sont acceptes"}), 400
            chemin = Config.TEMPLATES_USER_DIR / nom_fichier
            fichier.save(str(chemin))
            nom = request.form.get("name", nom_fichier.rsplit(".", 1)[0])
            description = request.form.get("description", "")
            contenu_yaml = chemin.read_text()

        # Cas 2 : contenu JSON (editeur en ligne)
        else:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "Donnees manquantes"}), 400
            nom = data.get("name", "").strip()
            description = data.get("description", "")
            contenu_yaml = data.get("content", "").strip()
            if not nom:
                return jsonify({"success": False, "error": "Le nom est obligatoire"}), 400
            if not contenu_yaml:
                return jsonify({"success": False, "error": "Le contenu YAML est obligatoire"}), 400
            nom_fichier = secure_filename(nom.replace(" ", "_")) + ".yaml"
            chemin = Config.TEMPLATES_USER_DIR / nom_fichier
            chemin.write_text(contenu_yaml)

        # Verification basique du YAML
        try:
            import yaml
            yaml.safe_load(contenu_yaml)
        except yaml.YAMLError as ye:
            chemin.unlink(missing_ok=True)
            return jsonify({"success": False, "error": f"YAML invalide : {ye}"}), 400

        template = Template(name=nom, description=description,
                            file_path=str(chemin), category="user")
        db.session.add(template)
        db.session.commit()
        logger.info(f"Template '{nom}' cree")
        return jsonify({"success": True, "template": template.to_dict()}), 201

    except Exception as e:
        logger.error(f"POST /api/templates : {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@template_bp.route("/<int:template_id>", methods=["PUT"])
def modifier_template(template_id):
    """Modifie le contenu d'un template utilisateur."""
    try:
        template = Template.query.get_or_404(template_id)
        if template.category == "builtin":
            return jsonify({"success": False, "error": "Les templates builtin ne sont pas modifiables"}), 403
        data = request.get_json()
        contenu = data.get("content", "")
        try:
            import yaml
            yaml.safe_load(contenu)
        except yaml.YAMLError as ye:
            return jsonify({"success": False, "error": f"YAML invalide : {ye}"}), 400
        with open(template.file_path, "w") as f:
            f.write(contenu)
        if data.get("name"):
            template.name = data["name"]
        if data.get("description") is not None:
            template.description = data["description"]
        db.session.commit()
        return jsonify({"success": True, "message": "Template mis a jour"})
    except Exception as e:
        logger.error(f"PUT /api/templates/{template_id} : {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@template_bp.route("/<int:template_id>", methods=["DELETE"])
def supprimer_template(template_id):
    try:
        template = Template.query.get_or_404(template_id)
        if template.category == "builtin":
            return jsonify({"success": False, "error": "Les templates builtin ne peuvent pas etre supprimes"}), 403
        if os.path.exists(template.file_path):
            os.remove(template.file_path)
        db.session.delete(template)
        db.session.commit()
        return jsonify({"success": True, "message": "Template supprime"})
    except Exception as e:
        logger.error(f"DELETE /api/templates/{template_id} : {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
