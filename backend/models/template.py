"""
Modele Template - Gestion des templates Heat
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from .database import Database

class Template:
    """Modele pour gerer les templates Heat"""

    @staticmethod
    def create(name: str, content: str, description: str = None,
               template_type: str = 'created', source_url: str = None,
               created_by: int = None, is_public: bool = False) -> int:
        """
        Creer un nouveau template

        Args:
            name: Nom unique du template
            content: Contenu YAML du template
            description: Description optionnelle
            template_type: Type ('builtin', 'git', 'uploaded', 'created')
            source_url: URL Git si type='git'
            created_by: ID de l'utilisateur createur
            is_public: Template accessible a tous

        Returns:
            ID du template cree
        """
        query = """
            INSERT INTO templates
            (name, description, content, type, source_url, created_by, is_public)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        return Database.execute_insert(
            query,
            (name, description, content, template_type, source_url, created_by, is_public)
        )

    @staticmethod
    def get_by_id(template_id: int) -> Optional[Dict[str, Any]]:
        """Recuperer un template par son ID"""
        query = """
            SELECT t.*, u.username as created_by_username
            FROM templates t
            LEFT JOIN users u ON t.created_by = u.id
            WHERE t.id = ?
        """
        templates = Database.execute_query(query, (template_id,))
        return templates[0] if templates else None

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        """Recuperer un template par son nom"""
        query = "SELECT * FROM templates WHERE name = ?"
        templates = Database.execute_query(query, (name,))
        return templates[0] if templates else None

    @staticmethod
    def get_all(user_id: int = None, include_public: bool = True) -> List[Dict[str, Any]]:
        """
        Recuperer tous les templates accessibles

        Args:
            user_id: ID utilisateur (pour filtrer ses templates prives)
            include_public: Inclure les templates publics
        """
        if user_id and include_public:
            query = """
                SELECT t.*, u.username as created_by_username
                FROM templates t
                LEFT JOIN users u ON t.created_by = u.id
                WHERE t.is_public = 1 OR t.created_by = ?
                ORDER BY t.created_at DESC
            """
            return Database.execute_query(query, (user_id,))
        elif user_id:
            query = """
                SELECT t.*, u.username as created_by_username
                FROM templates t
                LEFT JOIN users u ON t.created_by = u.id
                WHERE t.created_by = ?
                ORDER BY t.created_at DESC
            """
            return Database.execute_query(query, (user_id,))
        else:
            query = """
                SELECT t.*, u.username as created_by_username
                FROM templates t
                LEFT JOIN users u ON t.created_by = u.id
                WHERE t.is_public = 1
                ORDER BY t.created_at DESC
            """
            return Database.execute_query(query)

    @staticmethod
    def update(template_id: int, content: str = None, description: str = None,
               is_public: bool = None) -> bool:
        """Mettre a jour un template"""
        updates = []
        params = []

        if content is not None:
            updates.append("content = ?")
            params.append(content)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if is_public is not None:
            updates.append("is_public = ?")
            params.append(is_public)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(template_id)

        query = f"UPDATE templates SET {', '.join(updates)} WHERE id = ?"

        rows_affected = Database.execute_update(query, tuple(params))
        return rows_affected > 0

    @staticmethod
    def delete(template_id: int) -> bool:
        """Supprimer un template"""
        query = "DELETE FROM templates WHERE id = ?"
        rows_affected = Database.execute_update(query, (template_id,))
        return rows_affected > 0

    @staticmethod
    def get_builtin_templates() -> List[Dict[str, Any]]:
        """Recuperer uniquement les templates builtin"""
        query = """
            SELECT * FROM templates
            WHERE type = 'builtin'
            ORDER BY name
        """
        return Database.execute_query(query)
