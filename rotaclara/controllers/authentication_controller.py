from ..response import Response
from ..security.cookies import session_cookie


class AuthenticationController:
    def __init__(self, authentication, secure_cookie=False):
        self.authentication = authentication
        self.secure_cookie = secure_cookie

    def login(self, request):
        token = self.authentication.login(request.data, request.client)
        cookie = session_cookie(token, 28800, self.secure_cookie)
        return Response({'ok': True}, headers={'Set-Cookie': cookie})

    def current_user(self, request):
        fields = ('id', 'login', 'perfil', 'motorista_id', 'gerente_id')
        return Response({field: request.user[field] for field in fields})

    def logout(self, request):
        self.authentication.logout(request.token)
        cookie = session_cookie('', 0, self.secure_cookie)
        return Response({'ok': True}, headers={'Set-Cookie': cookie})
