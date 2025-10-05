from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib, base64

app = Flask(__name__)

# Clé AES-256 (32 bytes)
AES_KEY = get_random_bytes(32)  # en production, stocker de manière sécurisée

# ----------------- AES-GCM -----------------
def encrypt_gcm(plaintext: str, key: bytes) -> str:
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    blob = nonce + tag + ciphertext
    return base64.b64encode(blob).decode('utf-8')

def decrypt_gcm(blob_b64: str, key: bytes) -> str:
    blob = base64.b64decode(blob_b64)
    nonce = blob[:12]
    tag = blob[12:28]
    ciphertext = blob[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode('utf-8')

# ----------------- Routes -----------------
@app.route('/store', methods=['POST'])
def store_data():
    data = request.json.get('text')
    if not data:
        return jsonify({'error': 'Missing text'}), 400
    encrypted = encrypt_gcm(data, AES_KEY)
    # Ici tu pourrais stocker `encrypted` en DB
    return jsonify({'encrypted': encrypted})

@app.route('/retrieve', methods=['POST'])
def retrieve_data():
    encrypted = request.json.get('encrypted')
    if not encrypted:
        return jsonify({'error': 'Missing encrypted data'}), 400
    try:
        decrypted = decrypt_gcm(encrypted, AES_KEY)
        return jsonify({'decrypted': decrypted})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
