"""
Modele User - Gestion des utilisateurs
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .database import Database

class User:
    """Modele pour gerer les utilisateurs"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hasher un mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifier un mot de passe"""
        return secrets.compare_digest(
            User.hash_password(password),
            password_hash
        )

    @staticmethod
    def create(username: str, password: str, role: str = 'user',
               full_name: str = None, email: str = None) -> int:
        """
        Creer un nouvel utilisateur

        Returns:
            ID de l'utilisateur cree
        """
        password_hash = User.hash_password(password)

        query = """
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        """

        return Database.execute_insert(
            query,
            (username, password_hash, role, full_name, email)
        )

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authentifier un utilisateur

        Returns:
            Dictionnaire avec les infos utilisateur si succes, None sinon
        """
        query = """
            SELECT id, username, password_hash, role, full_name, email,
                   is_active, failed_attempts, locked_until
            FROM users
            WHERE username = ?
        """

        users = Database.execute_query(query, (username,))

        if not users:
            return None

        user = users[0]

        # Verifier si le compte est verrouille
        if user['locked_until']:
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                return None
            else:
                # Deverrouiller le compte
                User.reset_failed_attempts(user['id'])

        # Verifier si le compte est actif
        if not user['is_active']:
            return None

        # Verifier le mot de passe
        if not User.verify_password(password, user['password_hash']):
            User.increment_failed_attempts(user['id'])
            return None

        # Reinitialiser les tentatives echouees
        User.reset_failed_attempts(user['id'])

        # Mettre a jour last_login
        Database.execute_update(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user['id'])
        )

        # Retourner les infos utilisateur (sans le hash du mot de passe)
        return {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'full_name': user['full_name'],
            'email': user['email']
        }

    @staticmethod
    def increment_failed_attempts(user_id: int):
        """Incrementer le nombre de tentatives echouees"""
        from backend.config import Config

        query = "SELECT failed_attempts FROM users WHERE id = ?"
        result = Database.execute_query(query, (user_id,))

        if result:
            attempts = result[0]['failed_attempts'] + 1

            # Verrouiller le compte apres MAX_LOGIN_ATTEMPTS tentatives
            if attempts >= Config.MAX_LOGIN_ATTEMPTS:
                locked_until = datetime.now() + timedelta(seconds=Config.LOCKOUT_DURATION)
                Database.execute_update(
                    "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                    (attempts, locked_until.isoformat(), user_id)
                )
            else:
                Database.execute_update(
                    "UPDATE users SET failed_attempts = ? WHERE id = ?",
                    (attempts, user_id)
                )

    @staticmethod
    def reset_failed_attempts(user_id: int):
        """Reinitialiser les tentatives echouees"""
        Database.execute_update(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (user_id,)
        )

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Recuperer un utilisateur par son ID"""
        query = """
            SELECT id, username, role, full_name, email, created_at, last_login
            FROM users
            WHERE id = ?
        """
        users = Database.execute_query(query, (user_id,))
        return users[0] if users else None

    @staticmethod
    def get_all() -> list:
        """Recuperer tous les utilisateurs"""
        query = """
            SELECT id, username, role, full_name, email, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """
        return Database.execute_query(query)
