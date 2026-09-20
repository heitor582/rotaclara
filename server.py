"""Inicia o servidor local da RotaClara."""
import argparse
import os
from http.server import ThreadingHTTPServer

from rotaclara.application import Application
from rotaclara.bootstrap import PROJECT_ROOT, initialize_database, seed_demo
from rotaclara.database import Database
from rotaclara.http import create_handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Cria dados fictícios de demonstração')
    parser.add_argument('--port', type=int, default=8000)
    arguments = parser.parse_args()
    database = Database(os.environ.get('ROTACLARA_DB', PROJECT_ROOT / 'data/rotaclara.db'))
    initialize_database(database, os.environ.get('ROTACLARA_ADMIN_PASSWORD'))
    if arguments.demo:
        seed_demo(database)
    application = Application(database, secure_cookie=os.environ.get('ROTACLARA_SECURE_COOKIE') == '1')
    handler = create_handler(application, PROJECT_ROOT)
    with ThreadingHTTPServer(('127.0.0.1', arguments.port), handler) as server:
        print(f'RotaClara: http://127.0.0.1:{arguments.port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
