"""
Modele Stack - Gestion des stacks Heat deployees
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from .database import Database, json_to_db, db_to_json

class Stack:
    """Modele pour gerer les stacks Heat"""

    @staticmethod
    def create(stack_id: str, name: str, template_id: int = None,
               status: str = 'CREATE_IN_PROGRESS', parameters: dict = None,
               created_by: int = None) -> int:
        """
        Creer une nouvelle stack dans la base

        Args:
            stack_id: ID OpenStack de la stack
            name: Nom de la stack
            template_id: ID du template utilise
            status: Statut initial
            parameters: Parametres passes au template
            created_by: ID utilisateur

        Returns:
            ID de la stack en base
        """
        query = """
            INSERT INTO stacks
            (stack_id, name, template_id, status, created_by, parameters)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        return Database.execute_insert(
            query,
            (stack_id, name, template_id, status, created_by, json_to_db(parameters))
        )

    @staticmethod
    def get_by_id(db_id: int) -> Optional[Dict[str, Any]]:
        """Recuperer une stack par son ID base de donnees"""
        query = """
            SELECT s.*, t.name as template_name, u.username as created_by_username
            FROM stacks s
            LEFT JOIN templates t ON s.template_id = t.id
            LEFT JOIN users u ON s.created_by = u.id
            WHERE s.id = ? AND s.deleted_at IS NULL
        """
        stacks = Database.execute_query(query, (db_id,))
        if stacks:
            stack = stacks[0]
            stack['parameters'] = db_to_json(stack['parameters'])
            stack['outputs'] = db_to_json(stack['outputs'])
            return stack
        return None

    @staticmethod
    def get_by_stack_id(stack_id: str) -> Optional[Dict[str, Any]]:
        """Recuperer une stack par son ID OpenStack"""
        query = """
            SELECT s.*, t.name as template_name, u.username as created_by_username
            FROM stacks s
            LEFT JOIN templates t ON s.template_id = t.id
            LEFT JOIN users u ON s.created_by = u.id
            WHERE s.stack_id = ? AND s.deleted_at IS NULL
        """
        stacks = Database.execute_query(query, (stack_id,))
        if stacks:
            stack = stacks[0]
            stack['parameters'] = db_to_json(stack['parameters'])
            stack['outputs'] = db_to_json(stack['outputs'])
            return stack
        return None

    @staticmethod
    def get_all(user_id: int = None, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        Recuperer toutes les stacks

        Args:
            user_id: Filtrer par utilisateur
            include_deleted: Inclure les stacks supprimees
        """
        deleted_filter = "" if include_deleted else "AND s.deleted_at IS NULL"

        if user_id:
            query = f"""
                SELECT s.*, t.name as template_name, u.username as created_by_username
                FROM stacks s
                LEFT JOIN templates t ON s.template_id = t.id
                LEFT JOIN users u ON s.created_by = u.id
                WHERE s.created_by = ? {deleted_filter}
                ORDER BY s.created_at DESC
            """
            stacks = Database.execute_query(query, (user_id,))
        else:
            query = f"""
                SELECT s.*, t.name as template_name, u.username as created_by_username
                FROM stacks s
                LEFT JOIN templates t ON s.template_id = t.id
                LEFT JOIN users u ON s.created_by = u.id
                WHERE 1=1 {deleted_filter}
                ORDER BY s.created_at DESC
            """
            stacks = Database.execute_query(query)

        # Decoder les JSON
        for stack in stacks:
            stack['parameters'] = db_to_json(stack['parameters'])
            stack['outputs'] = db_to_json(stack['outputs'])

        return stacks

    @staticmethod
    def update_status(stack_id: str, status: str, outputs: dict = None) -> bool:
        """Mettre a jour le statut d'une stack"""
        if outputs is not None:
            query = """
                UPDATE stacks
                SET status = ?, outputs = ?, updated_at = ?
                WHERE stack_id = ?
            """
            params = (status, json_to_db(outputs), datetime.now().isoformat(), stack_id)
        else:
            query = """
                UPDATE stacks
                SET status = ?, updated_at = ?
                WHERE stack_id = ?
            """
            params = (status, datetime.now().isoformat(), stack_id)

        rows_affected = Database.execute_update(query, params)
        return rows_affected > 0

    @staticmethod
    def mark_deleted(stack_id: str) -> bool:
        """Marquer une stack comme supprimee (soft delete)"""
        query = """
            UPDATE stacks
            SET deleted_at = ?, updated_at = ?
            WHERE stack_id = ?
        """
        now = datetime.now().isoformat()
        rows_affected = Database.execute_update(query, (now, now, stack_id))
        return rows_affected > 0

    @staticmethod
    def get_statistics(user_id: int = None) -> Dict[str, Any]:
        """Obtenir des statistiques sur les stacks"""
        user_filter = "WHERE created_by = ? AND deleted_at IS NULL" if user_id else "WHERE deleted_at IS NULL"
        params = (user_id,) if user_id else ()

        query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status LIKE '%COMPLETE' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status LIKE '%IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status LIKE '%FAILED' THEN 1 ELSE 0 END) as failed
            FROM stacks
            {user_filter}
        """

        result = Database.execute_query(query, params)
        return result[0] if result else {
            'total': 0,
            'completed': 0,
            'in_progress': 0,
            'failed': 0
        }
