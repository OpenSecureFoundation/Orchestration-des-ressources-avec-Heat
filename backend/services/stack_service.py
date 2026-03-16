"""
Service de gestion des stacks Heat.
Gere la creation, la consultation et la suppression des stacks.
"""

import json
import logging
import os
from pathlib import Path

from backend.config import Config
from backend.models.database import db
from backend.models.stack import Stack
from backend.models.template import Template
from backend.services.openstack_service import OpenStackService

logger = logging.getLogger(__name__)


class StackService:
    """Gestion complete du cycle de vie des stacks Heat."""

    @staticmethod
    def create_stack(name: str, template_id: int, parameters: dict) -> dict:
        """
        Cree une stack Heat.
        Charge le template, injecte les parametres auto-detectes
        si manquants, puis soumet la creation a Heat.
        """
        try:
            # Recuperation du template en base
            template = Template.query.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} introuvable")

            # Lecture du contenu du template YAML
            with open(template.file_path, "r") as f:
                template_content = f.read()

            # Injection des parametres auto-detectes si absents
            if "public_network" not in parameters or not parameters["public_network"]:
                parameters["public_network"] = Config.PUBLIC_NETWORK_NAME

            if "dashboard_ip" not in parameters or not parameters["dashboard_ip"]:
                parameters["dashboard_ip"] = Config.get_dashboard_ip()

            if "image_name" not in parameters or not parameters["image_name"]:
                parameters["image_name"] = Config.DEFAULT_IMAGE

            if "flavor_name" not in parameters or not parameters["flavor_name"]:
                parameters["flavor_name"] = Config.DEFAULT_FLAVOR

            # Lecture des templates imbriques depuis le meme repertoire
            template_dir = str(Path(template.file_path).parent)
            fichiers_env = {}
            for fichier in os.listdir(template_dir):
                if fichier.endswith(".yaml") and fichier != Path(template.file_path).name:
                    chemin = os.path.join(template_dir, fichier)
                    with open(chemin, "r") as f:
                        fichiers_env[fichier] = f.read()

            # Creation de la stack via Heat
            hc = OpenStackService.get_heat_client()
            stack_heat = hc.stacks.create(
                stack_name=name,
                template=template_content,
                parameters=parameters,
                files=fichiers_env,
            )

            heat_id = stack_heat["stack"]["id"]

            # Enregistrement en base de donnees
            nouvelle_stack = Stack(
                heat_id=heat_id,
                name=name,
                status="CREATE_IN_PROGRESS",
                template_id=template_id,
                parameters=json.dumps(parameters),
            )
            db.session.add(nouvelle_stack)
            db.session.commit()

            logger.info(f"Stack '{name}' creee avec l'ID Heat : {heat_id}")
            return nouvelle_stack.to_dict()

        except Exception as e:
            logger.error(f"Erreur creation stack '{name}' : {e}")
            db.session.rollback()
            raise

    @staticmethod
    def list_all_stacks() -> list:
        """
        Liste toutes les stacks en combinant base de donnees et Heat.
        Met a jour les statuts depuis Heat.
        """
        try:
            hc = OpenStackService.get_heat_client()
            stacks_heat = {s.id: s for s in hc.stacks.list()}
        except Exception as e:
            logger.warning(f"Impossible de recuperer les stacks depuis Heat : {e}")
            stacks_heat = {}

        stacks_bdd = Stack.query.all()
        resultats = []

        for stack in stacks_bdd:
            data = stack.to_dict()
            # Mise a jour du statut depuis Heat
            if stack.heat_id and stack.heat_id in stacks_heat:
                data["status"] = stacks_heat[stack.heat_id].stack_status
                # Mise a jour en base
                stack.status = data["status"]
            resultats.append(data)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        return resultats

    @staticmethod
    def get_stack_status(stack_id: str) -> dict:
        """
        Recupere le statut actuel d'une stack depuis Heat.
        stack_id peut etre l'ID interne (int) ou le heat_id (UUID).
        """
        try:
            stack = Stack.query.filter(
                (Stack.heat_id == stack_id) | (Stack.id == stack_id)
            ).first()

            if not stack:
                raise ValueError(f"Stack '{stack_id}' introuvable en base")

            hc = OpenStackService.get_heat_client()
            stack_heat = hc.stacks.get(stack.heat_id)

            status = {
                "heat_id": stack.heat_id,
                "name": stack.name,
                "status": stack_heat.stack_status,
                "status_reason": getattr(stack_heat, "stack_status_reason", ""),
                "creation_time": getattr(stack_heat, "creation_time", None),
            }

            # Mise a jour en base
            stack.status = stack_heat.stack_status
            db.session.commit()

            return status

        except Exception as e:
            logger.error(f"Erreur statut stack '{stack_id}' : {e}")
            raise

    @staticmethod
    def delete_stack(stack_id: str) -> bool:
        """
        Supprime une stack dans Heat et dans la base de donnees.
        """
        try:
            stack = Stack.query.filter(
                (Stack.heat_id == stack_id) | (Stack.id == stack_id)
            ).first()

            if not stack:
                raise ValueError(f"Stack '{stack_id}' introuvable")

            # Suppression dans Heat
            if stack.heat_id:
                hc = OpenStackService.get_heat_client()
                hc.stacks.delete(stack.heat_id)
                logger.info(f"Stack '{stack.name}' supprimee dans Heat")

            # Suppression en base
            db.session.delete(stack)
            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"Erreur suppression stack '{stack_id}' : {e}")
            db.session.rollback()
            raise

    @staticmethod
    def get_stack_resources(stack_id: str) -> list:
        """Liste les ressources d'une stack Heat."""
        try:
            stack = Stack.query.filter(
                (Stack.heat_id == stack_id) | (Stack.id == stack_id)
            ).first()

            if not stack or not stack.heat_id:
                return []

            hc = OpenStackService.get_heat_client()
            ressources = hc.resources.list(stack.heat_id)

            return [
                {
                    "name": r.resource_name,
                    "type": r.resource_type,
                    "status": r.resource_status,
                    "physical_id": r.physical_resource_id,
                }
                for r in ressources
            ]

        except Exception as e:
            logger.error(f"Erreur ressources stack '{stack_id}' : {e}")
            return []

    @staticmethod
    def get_stack_outputs(stack_id: str) -> dict:
        """Recupere les outputs d'une stack Heat."""
        try:
            stack = Stack.query.filter(
                (Stack.heat_id == stack_id) | (Stack.id == stack_id)
            ).first()

            if not stack or not stack.heat_id:
                return {}

            hc = OpenStackService.get_heat_client()
            stack_heat = hc.stacks.get(stack.heat_id)
            outputs = getattr(stack_heat, "outputs", [])

            return {
                item["output_key"]: item.get("output_value")
                for item in outputs
            }

        except Exception as e:
            logger.error(f"Erreur outputs stack '{stack_id}' : {e}")
            return {}

    @staticmethod
    def get_stack_events(stack_id: str) -> list:
        """Recupere les evenements d'une stack Heat."""
        try:
            stack = Stack.query.filter(
                (Stack.heat_id == stack_id) | (Stack.id == stack_id)
            ).first()

            if not stack or not stack.heat_id:
                return []

            hc = OpenStackService.get_heat_client()
            evenements = hc.events.list(stack.heat_id)

            return [
                {
                    "id": e.id,
                    "resource_name": e.resource_name,
                    "resource_status": e.resource_status,
                    "resource_status_reason": getattr(e, "resource_status_reason", ""),
                    "event_time": str(getattr(e, "event_time", "")),
                }
                for e in evenements
            ]

        except Exception as e:
            logger.error(f"Erreur evenements stack '{stack_id}' : {e}")
            return []

    @staticmethod
    def update_stack(stack_id: str, parameters: dict) -> dict:
        """
        Met a jour les parametres d'une stack Heat existante.
        Utilise stack update pour modifier sans recrer.
        """
        try:
            stack = Stack.query.filter(
                (Stack.heat_id == stack_id) | (Stack.id == stack_id)
            ).first()
            if not stack:
                raise ValueError(f"Stack '{stack_id}' introuvable")

            # Recuperer le template actuel
            template = Template.query.get(stack.template_id)
            if not template:
                raise ValueError("Template de la stack introuvable")

            with open(template.file_path, "r") as f:
                template_content = f.read()

            # Fusionner les anciens parametres avec les nouveaux
            import json as _json
            anciens_params = {}
            try:
                anciens_params = _json.loads(stack.parameters or "{}")
            except Exception:
                pass
            anciens_params.update(parameters)

            # Injection auto des parametres manquants
            if "public_network" not in anciens_params:
                anciens_params["public_network"] = Config.PUBLIC_NETWORK_NAME
            if "dashboard_ip" not in anciens_params:
                anciens_params["dashboard_ip"] = Config.get_dashboard_ip()

            # Lecture des templates imbriques
            template_dir = str(Path(template.file_path).parent)
            fichiers_env = {}
            for fichier in os.listdir(template_dir):
                if fichier.endswith(".yaml") and fichier != Path(template.file_path).name:
                    chemin = os.path.join(template_dir, fichier)
                    with open(chemin, "r") as f:
                        fichiers_env[fichier] = f.read()

            hc = OpenStackService.get_heat_client()
            hc.stacks.update(
                stack.heat_id,
                template=template_content,
                parameters=anciens_params,
                files=fichiers_env,
            )

            stack.status = "UPDATE_IN_PROGRESS"
            stack.parameters = _json.dumps(anciens_params)
            db.session.commit()

            logger.info(f"Stack '{stack.name}' mise a jour")
            return stack.to_dict()

        except Exception as e:
            logger.error(f"Erreur update stack '{stack_id}' : {e}")
            db.session.rollback()
            raise

    @staticmethod
    def validate_template(template_content: str) -> dict:
        """
        Valide un template Heat via l'API OpenStack.
        Retourne un rapport de validation detaille.
        """
        # 1. Validation YAML basique
        try:
            import yaml
            parsed = yaml.safe_load(template_content)
        except Exception as ye:
            return {
                "success": False,
                "valid": False,
                "errors": [f"Erreur YAML : {ye}"],
                "warnings": [],
                "parameters": {},
            }

        errors = []
        warnings = []

        # 2. Verification structure HOT
        if not isinstance(parsed, dict):
            errors.append("Le template doit etre un dictionnaire YAML valide")
        else:
            if "heat_template_version" not in parsed:
                errors.append("Champ obligatoire manquant : heat_template_version")
            if "resources" not in parsed:
                errors.append("Champ obligatoire manquant : resources")
            elif not parsed.get("resources"):
                errors.append("La section 'resources' est vide")
            if "description" not in parsed:
                warnings.append("Bonne pratique : ajouter une 'description' au template")

        # 3. Validation via Heat API
        heat_errors = []
        try:
            hc = OpenStackService.get_heat_client()
            hc.stacks.validate(template=template_content)
        except Exception as e:
            msg = str(e)
            # Extraire le message utile depuis l'erreur Heat
            if "ERROR" in msg or "error" in msg.lower():
                heat_errors.append(f"Heat : {msg[:300]}")
            else:
                heat_errors.append(f"Heat : {msg[:300]}")

        errors.extend(heat_errors)

        # 4. Extraire les parametres pour affichage
        params_info = {}
        if isinstance(parsed, dict) and "parameters" in parsed:
            for pname, pdef in (parsed.get("parameters") or {}).items():
                if isinstance(pdef, dict):
                    params_info[pname] = {
                        "type": pdef.get("type", "string"),
                        "description": pdef.get("description", ""),
                        "default": pdef.get("default", None),
                        "required": "default" not in pdef,
                    }

        return {
            "success": True,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "parameters": params_info,
            "resources_count": len((parsed or {}).get("resources", {})) if isinstance(parsed, dict) else 0,
        }
