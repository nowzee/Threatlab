"""
API key management module for external integrations.

This module provides functions to create, list and update API keys
stored in encrypted form in the database.
"""
from typing import List, Dict, Any
from module.database.db_manager import DatabaseManagerUser
from module.crypto_utils.key_manager import Key_manager_db
from datetime import datetime


def verify_api_key(api_key: str) -> bool:
    """
    Check whether an API key exists in the database.

    Args:
        api_key (str): API key to check (encrypted).

    Returns:
        bool: True if the key exists, False otherwise.
    """
    with DatabaseManagerUser() as db:
        # Query database for existing encrypted API key (use backticks for 'key' reserved word)
        db.execute("SELECT id FROM api_keys WHERE `key` = ?", (api_key,))
        result = db.fetchone()
        return result is not None


class ManageApiKey:
    """
    API key management class for external integrations.

    This class allows adding, listing and updating API keys
    stored securely (encrypted) in the database.
    """

    def add(self, api_key: str, name: str, integration: str) -> bool:
        """
        Add a new API key to the database.

        The key is encrypted before being stored to guarantee its security.

        Args:
            api_key (str): Plaintext API key to add.
            name (str): Descriptive name of the API key.
            integration (str): Integration type (e.g.: "opencti", "elasticsearch").

        Returns:
            bool: True if the addition succeeded, False if the key already exists.
        """
        # Encrypt the API key using AES-GCM to protect sensitive data
        key_manager = Key_manager_db()
        cypher_api_key = key_manager.encrypt(api_key)

        # Check if this encrypted key already exists to prevent duplicates
        if verify_api_key(cypher_api_key):
            return False

        with DatabaseManagerUser() as db:
            # Store encrypted key with metadata (use backticks for 'key' reserved word)
            db.execute(
                "INSERT INTO api_keys (`key`, name, integration) VALUES (?, ?, ?)",
                (cypher_api_key, name, integration)
            )
        return True

    def list(self) -> List[Dict[str, Any]]:
        """
        List all registered API keys.

        The keys are decrypted before being returned.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing:
                - id: Key identifier
                - key: Decrypted API key
                - name: Key name
                - integration: Integration type
        """
        key_manager = Key_manager_db()
        with DatabaseManagerUser() as db:
            # Retrieve all encrypted API keys from database (use backticks for 'key' reserved word)
            db.execute("SELECT id, `key`, name, integration FROM api_keys")
            result = db.fetchall()

        # Decrypt each key before returning to user
        decrypted_results = []
        for row in result:
            decrypted_results.append({
                "id": row[0],
                "key": key_manager.decrypt(row[1]),  # Decrypt the encrypted key
                "name": row[2],
                "integration": row[3]
            })

        return decrypted_results

    def update(self, api_key: str, name: str, integration: str) -> bool:
        """
        Update the information of an existing API key.

        Args:
            api_key (str): Plaintext API key to update.
            name (str): New name for the key.
            integration (str): New integration type.

        Returns:
            bool: True if the update succeeded, False if the key does not exist.
        """
        # Encrypt the API key to match stored format
        key_manager = Key_manager_db()
        cypher_api_key = key_manager.encrypt(api_key)

        # Verify key exists before attempting update
        if not verify_api_key(cypher_api_key):
            return False

        with DatabaseManagerUser() as db:
            # Update metadata only, key itself remains unchanged (use backticks for 'key' reserved word)
            db.execute(
                "UPDATE api_keys SET name = ?, integration = ? WHERE `key` = ?",
                (name, integration, cypher_api_key)
            )
        return True
