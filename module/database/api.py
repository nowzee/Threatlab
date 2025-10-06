"""
Module de gestion des clés API pour les intégrations externes.

Ce module fournit des fonctions pour créer, lister et mettre à jour les clés API
stockées de manière chiffrée dans la base de données.
"""
from typing import Optional, List, Dict, Any
from module.database.db_manager import DatabaseManagerUser
from module.crypto_utils.key_manager import Key_manager_db
from datetime import datetime


def verify_api_key(api_key: str) -> bool:
    """
    Vérifie si une clé API existe dans la base de données.

    Args:
        api_key (str): Clé API à vérifier (chiffrée).

    Returns:
        bool: True si la clé existe, False sinon.
    """
    with DatabaseManagerUser() as db:
        db.execute("SELECT id FROM api_keys WHERE key = ?", (api_key,))
        result = db.fetchone()
        return result is not None


class ManageApiKey:
    """
    Classe de gestion des clés API pour les intégrations externes.

    Cette classe permet d'ajouter, lister et mettre à jour les clés API
    stockées de manière sécurisée (chiffrées) dans la base de données.
    """

    def add(self, api_key: str, name: str, integration: str) -> bool:
        """
        Ajoute une nouvelle clé API dans la base de données.

        La clé est chiffrée avant d'être stockée pour garantir sa sécurité.

        Args:
            api_key (str): Clé API en clair à ajouter.
            name (str): Nom descriptif de la clé API.
            integration (str): Type d'intégration (ex: "opencti", "elasticsearch").

        Returns:
            bool: True si l'ajout a réussi, False si la clé existe déjà.
        """
        key_manager = Key_manager_db()
        cypher_api_key = key_manager.encrypt(api_key)

        if verify_api_key(cypher_api_key):
            return False

        now = datetime.now()

        with DatabaseManagerUser() as db:
            db.execute(
                "INSERT INTO api_keys (key, name, integration, created_at) VALUES (?, ?, ?, ?)",
                (cypher_api_key, name, integration, now)
            )
        return True

    def list(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les clés API enregistrées.

        Les clés sont déchiffrées avant d'être retournées.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant:
                - id: Identifiant de la clé
                - key: Clé API déchiffrée
                - name: Nom de la clé
                - integration: Type d'intégration
        """
        key_manager = Key_manager_db()
        with DatabaseManagerUser() as db:
            db.execute("SELECT id, key, name, integration FROM api_keys")
            result = db.fetchall()

        # Déchiffre les clés avant de les retourner
        decrypted_results = []
        for row in result:
            decrypted_results.append({
                "id": row[0],
                "key": key_manager.decrypt(row[1]),
                "name": row[2],
                "integration": row[3]
            })

        return decrypted_results

    def update(self, api_key: str, name: str, integration: str) -> bool:
        """
        Met à jour les informations d'une clé API existante.

        Args:
            api_key (str): Clé API en clair à mettre à jour.
            name (str): Nouveau nom pour la clé.
            integration (str): Nouveau type d'intégration.

        Returns:
            bool: True si la mise à jour a réussi, False si la clé n'existe pas.
        """
        key_manager = Key_manager_db()
        cypher_api_key = key_manager.encrypt(api_key)

        if not verify_api_key(cypher_api_key):
            return False

        with DatabaseManagerUser() as db:
            db.execute(
                "UPDATE api_keys SET name = ?, integration = ? WHERE key = ?",
                (name, integration, cypher_api_key)
            )
        return True
