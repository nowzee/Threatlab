import re
from typing import Tuple

_PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).*$')

MIN_LENGTH = 12
MAX_LENGTH = 140


def validate_password(password: str):
    if not password:
        return False, 'Mot de passe requis'
    if len(password) < MIN_LENGTH:
        return False, f'Le mot de passe doit contenir au moins {MIN_LENGTH} caractères'
    if len(password) > MAX_LENGTH:
        return False, f'Le mot de passe ne doit pas dépasser {MAX_LENGTH} caractères'
    if not _PASSWORD_PATTERN.match(password):
        return False, ('Le mot de passe doit contenir au moins une lettre minuscule, '
                       'une majuscule, un chiffre et un caractère spécial')
    return True, ''
