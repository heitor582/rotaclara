import json
import logging
import sqlite3
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from .response import Response
from .security.errors import AuthenticationError
from .security.errors import LoginLimitExceeded

STATIC_ROUTES = {
    '/': 'index.html', '/campanha': 'campanha.html', '/documentacao': 'documentacao.html',
    '/documentacao/': 'documentacao.html', '/app.js': 'app.js', '/style.css': 'style.css',
    '/docs.css': 'docs.css', '/docs.js': 'docs.js', '/manifest.webmanifest': 'manifest.webmanifest',
    '/icon.svg': 'icon.svg', '/sw.js': 'sw.js',
    '/api.js': 'api.js', '/formatters.js': 'formatters.js', '/views.js': 'views.js',
    '/charts.js': 'charts.js', '/reporting.js': 'reporting.js',
}
CONTENT_TYPES = {'html': 'text/html; charset=utf-8', 'js': 'application/javascript; charset=utf-8',
                 'css': 'text/css; charset=utf-8', 'svg': 'image/svg+xml', 'webmanifest': 'application/manifest+json'}
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https://www.plantuml.com; connect-src 'self'; frame-ancestors 'none'; "
    "base-uri 'self'; form-action 'self'"
)


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def do_PUT(self):
        self.handle_request('PUT')

    def handle_request(self, method):
        try:
            parsed = urlparse(self.path)
            if not parsed.path.startswith('/api/'):
                response = self.serve_static(parsed.path) if method == 'GET' else Response({'erro': 'Método não permitido'}, 405)
            else:
                if method != 'GET':
                    self.validate_request_origin()
                response = self.application.dispatch(
                    method, parsed.path, parse_qs(parsed.query, keep_blank_values=True),
                    self.read_json_body() if method != 'GET' else {},
                    self.headers.get('Cookie', ''), self.client_address[0],
                )
        except AuthenticationError as error:
            response = Response({'erro': str(error)}, 401)
        except LoginLimitExceeded as error:
            response = Response({'erro': str(error)}, 429)
        except PermissionError as error:
            response = Response({'erro': str(error)}, 403)
        except (ValueError, KeyError, TypeError) as error:
            response = Response({'erro': str(error)}, 400)
        except sqlite3.IntegrityError:
            response = Response({'erro': 'Registro duplicado ou vínculo inválido. Confira os dados; '
                                 'só é permitido um roteiro por motorista e data.'}, 409)
        except Exception as error:
            logging.error('Falha interna: %s', type(error).__name__)
            response = Response({'erro': 'Não foi possível concluir a operação.'}, 500)
        self.send_response_data(response)

    def read_json_body(self):
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 < size <= 200000:
            raise ValueError('Tamanho da solicitação inválido.')
        try:
            data = json.loads(self.rfile.read(size))
        except (ValueError, UnicodeError):
            raise ValueError('JSON inválido.') from None
        if not isinstance(data, dict):
            raise ValueError('JSON inválido.')
        return data

    def validate_request_origin(self):
        origin = self.headers.get('Origin')
        host = self.headers.get('Host')
        if origin and origin not in (f'http://{host}', f'https://{host}'):
            raise PermissionError('Origem não autorizada')
        if self.headers.get('X-RotaClara') != '1':
            raise PermissionError('Cabeçalho de proteção ausente')

    def serve_static(self, path):
        documents = {f'/documentacao/arquivos/{file.name}': file for file in (self.project_root / 'docs').glob('*.md')}
        documents.update({f'/documentacao/arquivos/{file.name}': file
                          for file in (self.project_root / 'docs/diagramas').glob('*.puml')})
        for filename in ('schema.sql', 'README.md'):
            documents['/documentacao/arquivos/' + filename] = self.project_root / filename
        if path in documents:
            document = documents[path]
            return Response(document.read_bytes(), content_type='text/plain; charset=utf-8',
                            headers={'Content-Disposition': f'attachment; filename="{document.name}"'})
        filename = STATIC_ROUTES.get(path)
        if filename:
            return Response((self.project_root / 'static' / filename).read_bytes(),
                            content_type=CONTENT_TYPES[filename.rsplit('.', 1)[1]])
        return Response({'erro': 'Não encontrado'}, 404)

    def send_response_data(self, response):
        payload = response.data
        if response.content_type.startswith('application/json'):
            payload = json.dumps(payload, ensure_ascii=False).encode()
        elif isinstance(payload, str):
            payload = payload.encode()
        self.send_response(response.status)
        headers = {'Content-Type': response.content_type, 'Content-Length': str(len(payload)),
                   'Cache-Control': 'no-store' if self.path.startswith('/api/') else 'no-cache',
                   'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin',
                   'Content-Security-Policy': CONTENT_SECURITY_POLICY, **response.headers}
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)


def create_handler(application, project_root):
    class ConfiguredHandler(RequestHandler):
        pass
    ConfiguredHandler.application = application
    ConfiguredHandler.project_root = project_root
    return ConfiguredHandler
