"""
Module de gestion de la base de donnees SQLite
Fournit les fonctions de connexion et d'initialisation
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import json

class Database:
    """Classe singleton pour gerer la connexion a la base de donnees"""

    _instance = None
    _db_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, db_path: str):
        """Initialiser le chemin de la base de donnees"""
        cls._db_path = db_path

        # Creer le dossier si necessaire
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Creer les tables si la base n'existe pas
        if not os.path.exists(db_path):
            cls._create_database()

    @classmethod
    def _create_database(cls):
        """Creer la base de donnees avec le schema"""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'database',
            'schema.sql'
        )

        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema SQL non trouve: {schema_path}")

        with open(schema_path, 'r') as f:
            schema = f.read()

        conn = sqlite3.connect(cls._db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()

    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Context manager pour obtenir une connexion a la base de donnees
        Usage:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
        """
        if cls._db_path is None:
            raise RuntimeError("Database non initialisee. Appeler Database.initialize() d'abord")

        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row  # Permet d'acceder aux colonnes par nom
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def execute_query(cls, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Executer une requete SELECT et retourner les resultats

        Args:
            query: Requete SQL
            params: Parametres de la requete

        Returns:
            Liste de dictionnaires representant les lignes
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @classmethod
    def execute_insert(cls, query: str, params: tuple = ()) -> int:
        """
        Executer une requete INSERT et retourner l'ID insere

        Args:
            query: Requete SQL
            params: Parametres de la requete

        Returns:
            ID de la ligne inseree
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    @classmethod
    def execute_update(cls, query: str, params: tuple = ()) -> int:
        """
        Executer une requete UPDATE/DELETE et retourner le nombre de lignes affectees

        Args:
            query: Requete SQL
            params: Parametres de la requete

        Returns:
            Nombre de lignes affectees
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount


# Fonctions utilitaires pour convertir les donnees

def json_to_db(data: Any) -> str:
    """Convertir un objet Python en JSON pour stockage en base"""
    if data is None:
        return None
    return json.dumps(data)

def db_to_json(data: str) -> Any:
    """Convertir une chaine JSON de la base en objet Python"""
    if data is None:
        return None
    return json.loads(data)
