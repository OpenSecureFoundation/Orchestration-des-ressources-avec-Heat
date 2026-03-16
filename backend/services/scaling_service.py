"""
Service de scaling automatique.
"""
import logging
from datetime import datetime

from backend.models.database import db
from backend.models.scaling_policy import ScalingPolicy
from backend.models.scaling_history import ScalingHistory

logger = logging.getLogger(__name__)
FLAVORS_ORDRE = ["m1.small", "m1.medium", "m1.large"]


class ScalingService:

    @staticmethod
    def create_policy(server_id, server_name, metric, threshold_up, threshold_down, cooldown):
        try:
            p = ScalingPolicy.query.filter_by(server_id=server_id).first()
            if p:
                p.server_name = server_name; p.metric = metric
                p.threshold_up = threshold_up; p.threshold_down = threshold_down
                p.cooldown = cooldown; p.enabled = True
            else:
                p = ScalingPolicy(server_id=server_id, server_name=server_name,
                                  metric=metric, threshold_up=threshold_up,
                                  threshold_down=threshold_down, cooldown=cooldown)
                db.session.add(p)
            db.session.commit()
            return p.to_dict()
        except Exception as e:
            logger.error(f"Erreur creation politique : {e}")
            db.session.rollback(); raise

    @staticmethod
    def check_scaling_trigger(server_id, metrics):
        try:
            p = ScalingPolicy.query.filter_by(server_id=server_id, enabled=True).first()
            if not p:
                return "none"
            if p.last_scale_time:
                elapsed = (datetime.utcnow() - p.last_scale_time).total_seconds()
                if elapsed < p.cooldown:
                    return "none"
            valeur = metrics.get(p.metric)
            if valeur is None:
                return "none"
            if valeur >= p.threshold_up:
                logger.info(f"Scale UP: {server_id} {p.metric}={valeur}% >= {p.threshold_up}%")
                return "scale_up"
            if valeur <= p.threshold_down:
                logger.info(f"Scale DOWN: {server_id} {p.metric}={valeur}% <= {p.threshold_down}%")
                return "scale_down"
            return "none"
        except Exception as e:
            logger.error(f"Erreur check scaling : {e}")
            return "none"

    @staticmethod
    def execute_scaling(server_id, direction, metrics=None):
        from backend.services.vm_service import VMService
        flavor_avant = "inconnu"
        flavor_apres = "inconnu"
        metrique_nom = None
        valeur_metrique = None

        # Recuperer la metrique surveillee
        try:
            p = ScalingPolicy.query.filter_by(server_id=server_id).first()
            if p and metrics:
                metrique_nom = p.metric
                valeur_metrique = metrics.get(p.metric)
        except Exception:
            pass

        try:
            vm = VMService.get_vm_details(server_id)
            fi = vm.get("flavor", {})
            flavor_avant = fi.get("original_name") or fi.get("id", "inconnu")

            if flavor_avant not in FLAVORS_ORDRE:
                flavors_dispo = VMService.get_available_flavors()
                for f in flavors_dispo:
                    if f["id"] == flavor_avant or f["name"] == flavor_avant:
                        flavor_avant = f["name"]; break

            if flavor_avant not in FLAVORS_ORDRE:
                flavor_avant = FLAVORS_ORDRE[0]

            idx = FLAVORS_ORDRE.index(flavor_avant)
            if direction == "scale_up":
                if idx >= len(FLAVORS_ORDRE) - 1:
                    logger.info(f"VM '{server_id}' deja au max"); return False
                flavor_apres = FLAVORS_ORDRE[idx + 1]
            else:
                if idx <= 0:
                    logger.info(f"VM '{server_id}' deja au min"); return False
                flavor_apres = FLAVORS_ORDRE[idx - 1]

            logger.info(f"Scaling {direction}: {server_id} {flavor_avant} -> {flavor_apres}")
            VMService.resize_vm(server_id, flavor_apres)

            # Mise a jour cooldown
            p2 = ScalingPolicy.query.filter_by(server_id=server_id).first()
            if p2:
                p2.last_scale_time = datetime.utcnow()
                p2.last_scale_direction = direction

            # Enregistrer dans l'historique
            hist = ScalingHistory(
                server_id=server_id,
                server_name=vm.get("name", server_id),
                direction=direction,
                flavor_avant=flavor_avant,
                flavor_apres=flavor_apres,
                metrique=metrique_nom,
                valeur_metrique=valeur_metrique,
                statut="succes",
            )
            db.session.add(hist)
            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"Erreur scaling {server_id}: {e}")
            # Enregistrer l'echec
            try:
                hist = ScalingHistory(
                    server_id=server_id,
                    server_name=server_id,
                    direction=direction,
                    flavor_avant=flavor_avant,
                    flavor_apres=flavor_apres,
                    metrique=metrique_nom,
                    valeur_metrique=valeur_metrique,
                    statut="echec",
                    message=str(e),
                )
                db.session.add(hist)
                db.session.commit()
            except Exception:
                db.session.rollback()
            return False

    @staticmethod
    def check_and_execute(server_id, metrics):
        direction = ScalingService.check_scaling_trigger(server_id, metrics)
        if direction != "none":
            ScalingService.execute_scaling(server_id, direction, metrics)

    @staticmethod
    def get_history(server_id, limit=50):
        try:
            rows = (ScalingHistory.query
                    .filter_by(server_id=server_id)
                    .order_by(ScalingHistory.timestamp.desc())
                    .limit(limit).all())
            return [r.to_dict() for r in rows]
        except Exception as e:
            logger.error(f"Erreur historique scaling: {e}"); return []

    @staticmethod
    def get_policy(server_id):
        try:
            p = ScalingPolicy.query.filter_by(server_id=server_id).first()
            return p.to_dict() if p else {}
        except Exception as e:
            logger.error(f"Erreur get_policy: {e}"); return {}

    @staticmethod
    def list_all_policies():
        try:
            return [p.to_dict() for p in ScalingPolicy.query.all()]
        except Exception as e:
            logger.error(f"Erreur list_all_policies: {e}"); return []

    @staticmethod
    def delete_policy(server_id):
        try:
            p = ScalingPolicy.query.filter_by(server_id=server_id).first()
            if not p: return False
            db.session.delete(p); db.session.commit(); return True
        except Exception as e:
            logger.error(f"Erreur delete_policy: {e}"); db.session.rollback(); return False
