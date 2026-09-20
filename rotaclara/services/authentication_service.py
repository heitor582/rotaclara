import secrets

from ..security.errors import AuthenticationError
from ..security.passwords import hash_token, verify_password

class AuthenticationService:
    def __init__(self, accounts, limiter, clock):
        self.accounts = accounts
        self.limiter = limiter
        self.clock = clock

    def login(self, data, client):
        timestamp = self.clock.now().timestamp()
        self.limiter.check(client, timestamp)
        login, password = data.get('login'), data.get('senha')
        if not isinstance(login, str) or not isinstance(password, str):
            raise ValueError('Informe usuário e senha válidos.')
        account = self.accounts.find_by_login(login)
        if not account or not verify_password(password, account['senha_hash']):
            self.limiter.record_failure(client, timestamp)
            raise AuthenticationError('Login ou senha incorretos.')
        self.limiter.clear(client)
        token = secrets.token_urlsafe(32)
        self.accounts.create_session(hash_token(token), account['id'], timestamp + 28800, timestamp)
        return token

    def authenticate(self, token):
        user = self.accounts.find_session_user(hash_token(token), self.clock.now().timestamp()) if token else None
        if not user:
            raise AuthenticationError('Entre para continuar.')
        return user

    def logout(self, token):
        self.accounts.delete_session(hash_token(token))
