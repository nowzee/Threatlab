"""
Module de gestion du chiffrement AES pour les données sensibles.

Ce module fournit une classe pour chiffrer et déchiffrer des données
en utilisant AES-GCM avec une clé stockée de manière sécurisée.
"""
import base64
import os
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES


class Key_manager_db:
    """
    Gestionnaire de chiffrement AES-GCM pour les données sensibles de la base de données.

    Cette classe gère une clé AES de 256 bits stockée dans un fichier '.key'.
    Elle utilise le mode GCM (Galois/Counter Mode) pour garantir à la fois
    la confidentialité et l'intégrité des données chiffrées.

    Attributes:
        AES_KEY (bytes): Clé AES de 256 bits utilisée pour le chiffrement/déchiffrement.
    """

    def __init__(self) -> None:
        """
        Initialise le gestionnaire de clés.

        Charge la clé AES depuis le fichier '.key' ou en crée une nouvelle
        si le fichier n'existe pas.
        """

        if not os.path.exists('secrets/.key'):
            # Generate a new 256-bit (32 bytes) AES key for first-time setup
            with open('secrets/.key', 'wb') as f:
                # Store key as base64 for easier file handling
                f.write(base64.b64encode(get_random_bytes(32)))

        # Load and decode the AES key from file
        with open('secrets/.key', 'rb') as f:
            self.AES_KEY = base64.b64decode(f.read())

    def encrypt(self, data: str) -> str:
        """
        Chiffre une chaîne de caractères en utilisant AES-GCM.

        Le chiffrement génère un nonce aléatoire de 12 octets, un tag d'authentification
        de 16 octets, et le texte chiffré. Ces éléments sont concaténés et encodés en base64.

        Args:
            data (str): Données en clair à chiffrer.

        Returns:
            str: Données chiffrées encodées en base64 (nonce + tag + ciphertext).
        """
        # Generate random 12-byte nonce (number used once) for GCM mode
        nonce = get_random_bytes(12)
        # Initialize AES cipher in GCM mode (provides both encryption and authentication)
        cipher = AES.new(self.AES_KEY, AES.MODE_GCM, nonce=nonce)
        # Encrypt and generate 16-byte authentication tag in one operation
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
        # Concatenate: nonce (12 bytes) + tag (16 bytes) + ciphertext (variable)
        # This format allows decryption since nonce and tag are needed
        blob = nonce + tag + ciphertext

        # Encode as base64 for safe storage in database/text fields
        return base64.b64encode(blob).decode('utf-8')

    def decrypt(self, data: str) -> str:
        """
        Déchiffre des données chiffrées avec AES-GCM.

        Extrait le nonce, le tag d'authentification et le texte chiffré depuis
        les données encodées en base64, puis déchiffre et vérifie l'intégrité.

        Args:
            data (str): Données chiffrées encodées en base64.

        Returns:
            str: Données déchiffrées en clair.

        Raises:
            ValueError: Si le tag d'authentification ne correspond pas (données altérées).
        """
        # Decode from base64 to get raw bytes
        blob = base64.b64decode(data)
        # Extract components from concatenated blob
        nonce = blob[:12]        # First 12 bytes: nonce
        tag = blob[12:28]        # Next 16 bytes: authentication tag
        ciphertext = blob[28:]   # Remaining bytes: actual encrypted data

        # Initialize cipher with same nonce used during encryption
        cipher = AES.new(self.AES_KEY, AES.MODE_GCM, nonce=nonce)
        # Decrypt and verify tag in one operation (will raise ValueError if tampered)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode('utf-8')
