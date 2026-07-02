"""
AES encryption management module for sensitive data.

This module provides a class to encrypt and decrypt data
using AES-GCM with a securely stored key.
"""
import base64
import os
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES


class Key_manager_db:
    """
    AES-GCM encryption manager for sensitive database data.

    This class manages a 256-bit AES key stored in a '.key' file.
    It uses GCM mode (Galois/Counter Mode) to guarantee both
    the confidentiality and the integrity of the encrypted data.

    Attributes:
        AES_KEY (bytes): 256-bit AES key used for encryption/decryption.
    """

    def __init__(self) -> None:
        """
        Initialize the key manager.

        Loads the AES key from the '.key' file or creates a new one
        if the file does not exist.
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
        Encrypt a string using AES-GCM.

        Encryption generates a random 12-byte nonce, a 16-byte authentication
        tag, and the ciphertext. These elements are concatenated and base64-encoded.

        Args:
            data (str): Plaintext data to encrypt.

        Returns:
            str: Base64-encoded encrypted data (nonce + tag + ciphertext).
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
        Decrypt data encrypted with AES-GCM.

        Extracts the nonce, the authentication tag and the ciphertext from
        the base64-encoded data, then decrypts and verifies integrity.

        Args:
            data (str): Base64-encoded encrypted data.

        Returns:
            str: Decrypted plaintext data.

        Raises:
            ValueError: If the authentication tag does not match (tampered data).
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
