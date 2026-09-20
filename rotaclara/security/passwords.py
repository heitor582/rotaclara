import hashlib
import hmac
import secrets

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000).hex()
    return f'{salt}:{digest}'


def verify_password(password, stored_hash):
    return hmac.compare_digest(stored_hash, hash_password(password, stored_hash.split(':')[0]))


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
