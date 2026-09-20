from http.cookies import CookieError, SimpleCookie


def session_token(cookie_header):
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
    except CookieError:
        return ''
    return cookie['rotaclara'].value if 'rotaclara' in cookie else ''


def session_cookie(token, max_age, secure=False):
    secure_attribute = '; Secure' if secure else ''
    return f'rotaclara={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={max_age}{secure_attribute}'
