"""
Fonctions de validation des donnees
"""

from typing import Dict, Any
import yaml

def validate_metrics_alert(data: dict, required_fields: list) -> Dict[str, Any]:
    """
    Valider les donnees d'une alerte de metriques

    Args:
        data: Donnees a valider
        required_fields: Liste des champs obligatoires

    Returns:
        {'valid': bool, 'error': str or None}
    """
    # Verifier les champs obligatoires
    for field in required_fields:
        if field not in data:
            return {
                'valid': False,
                'error': f'Champ obligatoire manquant: {field}'
            }

    # Valider le format des valeurs numeriques
    numeric_fields = ['cpu', 'ram', 'disk', 'network_in', 'network_out', 'network_latency']

    for field in numeric_fields:
        if field in data:
            try:
                value = float(data[field])

                # Valider les plages pour les pourcentages
                if field in ['cpu', 'ram', 'disk']:
                    if value < 0 or value > 100:
                        return {
                            'valid': False,
                            'error': f'{field} doit etre entre 0 et 100'
                        }

                # Valider que les valeurs sont positives
                if value < 0:
                    return {
                        'valid': False,
                        'error': f'{field} doit etre positif'
                    }

            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error': f'{field} doit etre un nombre'
                }

    # Valider le timestamp
    if 'timestamp' in data:
        try:
            int(data['timestamp'])
        except (ValueError, TypeError):
            return {
                'valid': False,
                'error': 'timestamp doit etre un entier (Unix timestamp)'
            }

    return {
        'valid': True,
        'error': None
    }


def validate_yaml_template(content: str) -> Dict[str, Any]:
    """
    Valider la syntaxe et la structure d'un template Heat YAML

    Args:
        content: Contenu YAML du template

    Returns:
        {'valid': bool, 'error': str or None, 'parsed': dict or None}
    """
    try:
        # Parser le YAML
        parsed = yaml.safe_load(content)

        # Verifier que c'est un dictionnaire
        if not isinstance(parsed, dict):
            return {
                'valid': False,
                'error': 'Le template doit etre un objet YAML (dictionnaire)',
                'parsed': None
            }

        # Verifier les champs obligatoires Heat
        required_fields = ['heat_template_version', 'resources']

        for field in required_fields:
            if field not in parsed:
                return {
                    'valid': False,
                    'error': f'Champ obligatoire manquant: {field}',
                    'parsed': None
                }

        # Verifier que resources est un dictionnaire
        if not isinstance(parsed['resources'], dict):
            return {
                'valid': False,
                'error': 'La section resources doit etre un dictionnaire',
                'parsed': None
            }

        # Verifier que resources n'est pas vide
        if not parsed['resources']:
            return {
                'valid': False,
                'error': 'La section resources ne peut pas etre vide',
                'parsed': None
            }

        return {
            'valid': True,
            'error': None,
            'parsed': parsed
        }

    except yaml.YAMLError as e:
        return {
            'valid': False,
            'error': f'Erreur de syntaxe YAML: {str(e)}',
            'parsed': None
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'Erreur lors de la validation: {str(e)}',
            'parsed': None
        }
