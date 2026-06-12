"""Password hashing with Argon2id."""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_ph = PasswordHasher()


def hash_password(plain: str) -> str:
    """Return the encoded Argon2id hash (salt included) of a password."""
    return _ph.hash(plain)


def verify_password(stored_hash: str, plain: str) -> bool:
    """Verify a password against a stored Argon2id hash."""
    try:
        return _ph.verify(stored_hash, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
