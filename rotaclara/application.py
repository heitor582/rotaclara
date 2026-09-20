from .dependencies import build_request_dependencies
from .clock import SystemClock
from .endpoints import resolve_endpoint
from .request import Request
from .response import Response
from .security.cookies import session_token
from .security.login_rate_limiter import LoginRateLimiter


class Application:
    def __init__(self, database, clock=None, secure_cookie=False):
        self.database = database
        self.clock = clock or SystemClock()
        self.secure_cookie = secure_cookie
        self.login_limiter = LoginRateLimiter()

    def dispatch(self, method, path, query, data, cookie_header, client):
        request = Request(query, data, client, session_token(cookie_header))
        with self.database.transaction(write=method != 'GET') as connection:
            authentication, endpoints = build_request_dependencies(
                connection, self.clock, self.login_limiter, self.secure_cookie,
            )
            endpoint, parameters = resolve_endpoint(endpoints, method, path)
            if endpoint is None or endpoint.requires_authentication:
                request.user = authentication.authenticate(request.token)
            if endpoint is None:
                return Response({'erro': 'Operação não encontrada'}, status=404)
            return endpoint.handler(request, **parameters)
