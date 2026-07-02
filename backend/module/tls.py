"""
Persistent self-signed TLS certificate generation.

Replaces the old `ssl_context='adhoc'` of the Flask dev server (which
regenerated a certificate on every start) with a stable certificate stored in
the secrets volume, served by gunicorn via certfile/keyfile. Agents connect with
`verify=False`, so the certificate does not need to be signed by a CA.
"""
import os
import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def ensure_self_signed_cert(cert_path: str, key_path: str) -> None:
    """Generate a self-signed certificate if it does not already exist."""
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return

    os.makedirs(os.path.dirname(cert_path), exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "threatlab")])
    now = datetime.datetime.utcnow()

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"[tls] self-signed certificate generated: {cert_path}")
