import base64, os
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES

class Key_manager_db:
    def __init__(self):
        if not os.path.exists('.key'):
            with open('.key', 'wb') as f:
                f.write(base64.b64encode(get_random_bytes(32)))

        with open('.key', 'rb') as f:
            self.AES_KEY = base64.b64decode(f.read())

    def encrypt(self, data):
        nonce = get_random_bytes(12)
        cipher = AES.new(self.AES_KEY, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
        blob = nonce + tag + ciphertext

        return base64.b64encode(blob).decode('utf-8')

    def decrypt(self, data):
        blob = base64.b64decode(data)
        nonce = blob[:12]
        tag = blob[12:28]
        ciphertext = blob[28:]

        cipher = AES.new(self.AES_KEY, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode('utf-8')