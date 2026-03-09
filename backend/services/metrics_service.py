"""
Service de gestion des metriques
Gere la collecte, le stockage et l'analyse des metriques
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
from backend.models.metrics import Metric, ScalingPolicy
from backend.services.vm_service import VMService
from backend.config import Config

class MetricsService:
    """Service de gestion des metriques"""

    @staticmethod
    def validate_alert(alert_data: dict, expected_token: str) -> Dict[str, Any]:
        """
        Valider une alerte recue d'un agent
        """
        # Verifier le token
        if alert_data.get('token') != expected_token:
            return {
                'valid': False,
                'reason': 'Token invalide',
                'metrics': None
            }

        # Verifier les champs obligatoires
        required_fields = ['source', 'timestamp']
        for field in required_fields:
            if field not in alert_data:
                return {
                    'valid': False,
                    'reason': f'Champ {field} manquant',
                    'metrics': None
                }

        # Verifier la fraicheur de l'alerte (anti-replay)
        try:
            alert_timestamp = int(alert_data['timestamp'])
            now = int(datetime.now().timestamp())

            if abs(now - alert_timestamp) > 60:
                return {
                    'valid': False,
                    'reason': 'Alerte trop ancienne (> 60s)',
                    'metrics': None
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'reason': 'Timestamp invalide',
                'metrics': None
            }

        # Extraire et valider les metriques
        metrics = {}
        available_metrics = Config.AVAILABLE_METRICS

        for metric_type, metric_config in available_metrics.items():
            if metric_type not in alert_data:
                continue

            try:
                value = float(alert_data[metric_type])

                # Valider les plages
                if metric_config['min'] is not None and value < metric_config['min']:
                    return {
                        'valid': False,
                        'reason': f'{metric_type} hors limites (min: {metric_config["min"]})',
                        'metrics': None
                    }

                if metric_config['max'] is not None and value > metric_config['max']:
                    return {
                        'valid': False,
                        'reason': f'{metric_type} hors limites (max: {metric_config["max"]})',
                        'metrics': None
                    }

                metrics[metric_type] = {
                    'value': value,
                    'unit': metric_config['unit']
                }

            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'reason': f'Valeur {metric_type} invalide',
                    'metrics': None
                }

        if not metrics:
            return {
                'valid': False,
                'reason': 'Aucune metrique valide trouvee',
                'metrics': None
            }

        return {
            'valid': True,
            'reason': None,
            'metrics': metrics
        }

    @staticmethod
    def save_metrics(server_id: str, server_name: str, metrics: dict):
        """
        Sauvegarder les metriques en base de donnees
        """
        for metric_type, metric_data in metrics.items():
            Metric.save(
                server_id=server_id,
                server_name=server_name,
                metric_type=metric_type,
                value=metric_data['value'],
                unit=metric_data['unit'],
                source='agent'
            )

    @staticmethod
    def determine_scaling_action(server_id: str, metrics: dict) -> Dict[str, Any]:
        """
        Determiner l'action de scaling a effectuer
        """
        policy = ScalingPolicy.get_by_server(server_id)

        if not policy or not policy['enabled']:
            return {
                'action': 'none',
                'metric': None,
                'value': None,
                'reason': 'Aucune politique active'
            }

        last_event = ScalingPolicy.get_last_scaling_event(server_id)

        if last_event:
            last_time = datetime.fromisoformat(last_event['timestamp'])
            cooldown_end = last_time + timedelta(seconds=policy['cooldown_seconds'])

            if datetime.now() < cooldown_end:
                remaining = int((cooldown_end - datetime.now()).total_seconds())
                return {
                    'action': 'cooldown',
                    'metric': None,
                    'value': None,
                    'reason': f'Cooldown actif ({remaining}s restantes)'
                }

        metric_type = policy['metric_type']

        if metric_type not in metrics:
            return {
                'action': 'none',
                'metric': metric_type,
                'value': None,
                'reason': f'Metrique {metric_type} non disponible'
            }

        value = metrics[metric_type]['value']

        if value >= policy['scale_up_threshold']:
            return {
                'action': 'scale_up',
                'metric': metric_type,
                'value': value,
                'reason': f'{metric_type} {value}% >= seuil {policy["scale_up_threshold"]}%'
            }
        elif value <= policy['scale_down_threshold']:
            return {
                'action': 'scale_down',
                'metric': metric_type,
                'value': value,
                'reason': f'{metric_type} {value}% <= seuil {policy["scale_down_threshold"]}%'
            }
        else:
            return {
                'action': 'none',
                'metric': metric_type,
                'value': value,
                'reason': f'{metric_type} dans les limites normales'
            }

    @staticmethod
    def get_next_flavor(current_flavor_name: str, action: str) -> Optional[str]:
        """
        Determiner le prochain flavor pour le scaling

        Args:
            current_flavor_name: Nom du flavor actuel (m1.small, m1.medium, m1.large)
            action: 'scale_up' ou 'scale_down'

        Returns:
            Nom du nouveau flavor ou None
        """
        # Ordre des flavors (NOM uniquement)
        flavor_order = ['m1.small', 'm1.medium', 'm1.large']

        try:
            current_index = flavor_order.index(current_flavor_name)
        except ValueError:
            print(f"[SCALING] Flavor actuel inconnu: {current_flavor_name}")
            return None

        if action == 'scale_up':
            if current_index < len(flavor_order) - 1:
                new_flavor = flavor_order[current_index + 1]
                print(f"[SCALING] Scale UP: {current_flavor_name} -> {new_flavor}")
                return new_flavor
            else:
                print(f"[SCALING] Deja au flavor maximum: {current_flavor_name}")
                return None

        elif action == 'scale_down':
            if current_index > 0:
                new_flavor = flavor_order[current_index - 1]
                print(f"[SCALING] Scale DOWN: {current_flavor_name} -> {new_flavor}")
                return new_flavor
            else:
                print(f"[SCALING] Deja au flavor minimum: {current_flavor_name}")
                return None

        return None

    @staticmethod
    def execute_scaling(server_id: str, action: str, current_flavor: str,
                       trigger_metric: str, trigger_value: float) -> Dict[str, Any]:
        """
        Executer une action de scaling

        Args:
            server_id: ID du serveur
            action: 'scale_up' ou 'scale_down'
            current_flavor: Nom du flavor actuel
            trigger_metric: Metrique qui a declenche le scaling
            trigger_value: Valeur de la metrique

        Returns:
            Dictionnaire avec success, message, new_flavor
        """
        # Determiner le nouveau flavor
        new_flavor_name = MetricsService.get_next_flavor(current_flavor, action)

        if not new_flavor_name:
            message = f'Impossible de scaler: deja au flavor {"maximum" if action == "scale_up" else "minimum"}'

            ScalingPolicy.log_scaling_event(
                server_id=server_id,
                event_type='rejected',
                old_flavor=current_flavor,
                new_flavor=None,
                trigger_metric=trigger_metric,
                trigger_value=trigger_value,
                success=False,
                message=message
            )

            return {
                'success': False,
                'message': message,
                'new_flavor': current_flavor
            }

        # Executer le resize
        print(f"[SCALING] Execution resize: {server_id} -> {new_flavor_name}")
        resize_result = VMService.resize_server(server_id, new_flavor_name)

        if not resize_result['success']:
            message = f'Erreur resize: {resize_result["error"]}'

            ScalingPolicy.log_scaling_event(
                server_id=server_id,
                event_type='rejected',
                old_flavor=current_flavor,
                new_flavor=new_flavor_name,
                trigger_metric=trigger_metric,
                trigger_value=trigger_value,
                success=False,
                message=message
            )

            return {
                'success': False,
                'message': message,
                'new_flavor': current_flavor
            }

        # Resize reussi - attendre et confirmer
        print(f"[SCALING] Attente 10s avant confirmation...")
        time.sleep(10)

        confirm_result = VMService.confirm_resize(server_id)
        print(f"[SCALING] Confirmation: {confirm_result}")

        # Logger le succes
        message = f'Resize de {current_flavor} vers {new_flavor_name} demarre'

        ScalingPolicy.log_scaling_event(
            server_id=server_id,
            event_type=action,
            old_flavor=current_flavor,
            new_flavor=new_flavor_name,
            trigger_metric=trigger_metric,
            trigger_value=trigger_value,
            success=True,
            message=message
        )

        print(f"[SCALING] Succes: {message}")

        return {
            'success': True,
            'message': message,
            'new_flavor': new_flavor_name
        }
