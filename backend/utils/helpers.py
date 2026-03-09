"""
Fonctions utilitaires diverses
"""

from flask import jsonify
from typing import Any, Dict
from datetime import datetime
from backend.models.database import Database

def success_response(data: Any = None, message: str = None) -> tuple:
    """
    Generer une reponse JSON de succes standardisee

    Args:
        data: Donnees a retourner
        message: Message optionnel

    Returns:
        (response, status_code)
    """
    response = {
        'success': True
    }

    if data is not None:
        response['data'] = data

    if message:
        response['message'] = message

    return jsonify(response), 200


def error_response(error: str, status_code: int = 400, details: Dict = None) -> tuple:
    """
    Generer une reponse JSON d'erreur standardisee

    Args:
        error: Message d'erreur
        status_code: Code HTTP
        details: Details supplementaires

    Returns:
        (response, status_code)
    """
    response = {
        'success': False,
        'error': error
    }

    if details:
        response['details'] = details

    return jsonify(response), status_code


def log_action(user_id: int = None, category: str = 'general',
               level: str = 'INFO', message: str = '', details: Dict = None):
    """
    Logger une action dans la base de donnees

    Args:
        user_id: ID de l'utilisateur (None pour actions systeme)
        category: Categorie ('auth', 'stack', 'scaling', 'template', etc.)
        level: Niveau ('INFO', 'WARNING', 'ERROR')
        message: Message descriptif
        details: Details supplementaires (stockes en JSON)
    """
    from backend.models.database import json_to_db

    query = """
        INSERT INTO system_logs (level, category, message, details, user_id)
        VALUES (?, ?, ?, ?, ?)
    """

    Database.execute_insert(
        query,
        (level, category, message, json_to_db(details), user_id)
    )


def format_timestamp(timestamp: str) -> str:
    """
    Formater un timestamp ISO en format lisible

    Args:
        timestamp: Timestamp au format ISO

    Returns:
        Timestamp formate (ex: "22/02/2026 14:30")
    """
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return timestamp


def get_client_ip() -> str:
    """
    Obtenir l'IP du client depuis la requete Flask

    Returns:
        Adresse IP
    """
    from flask import request

    # Gerer les proxies
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr
