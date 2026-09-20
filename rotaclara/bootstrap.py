import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .clock import SystemClock
from .domain import LOCAL_TIMEZONE
from .repositories.audit_repository import AuditRepository
from .repositories.parameter_repository import ParameterRepository
from .repositories.route_repository import RouteRepository
from .repositories.team_repository import TeamRepository
from .security.passwords import hash_password
from .services.route_service import RouteService

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def initialize_database(database, admin_password=None):
    database.path.parent.mkdir(parents=True, exist_ok=True)
    with database.transaction(write=True) as connection:
        connection.executescript((PROJECT_ROOT / 'schema.sql').read_text())
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('INSERT OR IGNORE INTO parametro VALUES (1,6.19,10,0.619,8,1,?)', ('saida_menos_chegada',))
        if not connection.execute('SELECT id FROM usuario LIMIT 1').fetchone():
            password = admin_password or secrets.token_urlsafe(12)
            connection.execute('INSERT INTO usuario(login,senha_hash,perfil) VALUES (?,?,?)',
                               ('admin', hash_password(password), 'administrador'))
            print(f'Primeiro acesso: admin / {password}', flush=True)
    os.chmod(database.path, 0o600)


def seed_demo(database, clock=None):
    clock = clock or SystemClock()
    with database.transaction(write=True) as connection:
        if connection.execute('SELECT id FROM motorista LIMIT 1').fetchone():
            return
        manager_id = connection.execute('INSERT INTO gerente(nome,telefone,email) VALUES (?,?,?)',
                                        ('Marina Demo', '31900000000', 'marina@example.invalid')).lastrowid
        drivers = []
        for number, name, vehicle in [(1, 'Lucas Demo', 'Van • DEMO-001'), (2, 'Ana Demo', 'Moto • DEMO-002')]:
            driver_id = connection.execute('INSERT INTO motorista(gerente_id,nome,telefone,documento,veiculo,km_por_litro) '
                                           'VALUES (?,?,?,?,?,?)', (manager_id, name, '31900000000', f'DEMO-{number}',
                                            vehicle, 10 if number == 1 else 30)).lastrowid
            drivers.append(driver_id)
        credentials = []
        for login, role, driver_id, account_manager_id in [
            ('gerente', 'gerente', None, manager_id), ('motorista', 'motorista', drivers[0], None)
        ]:
            password = secrets.token_urlsafe(10)
            connection.execute('INSERT INTO usuario(login,senha_hash,perfil,motorista_id,gerente_id) VALUES (?,?,?,?,?)',
                               (login, hash_password(password), role, driver_id, account_manager_id))
            credentials.append(f'{login}: {password}')
        routes = RouteRepository(connection)
        service = RouteService(routes, TeamRepository(connection), ParameterRepository(connection),
                               AuditRepository(connection), clock)
        today = clock.now().astimezone(LOCAL_TIMEZONE).date()
        addresses = ['Base • Seg. Família', 'Rua Peru, 55', 'Rua X, 5', 'Av. João César']
        for days_ago in range(7):
            for number, driver_id in enumerate(drivers, 1):
                day = today - timedelta(days=days_ago)
                efficiency = 10 if number == 1 else 30
                route_id = routes.create(str(day), driver_id, 42 + days_ago * 3 + number * 4,
                                         {'valor_combustivel': 6.19, 'jornada_padrao_horas': 8}, efficiency)
                arrival = datetime.combine(day, datetime.min.time(), LOCAL_TIMEZONE).replace(hour=8)
                durations = [0, 15, 10, 50] if number == 1 else [0, 10, 5, 26]
                for order, (address, minutes) in enumerate(zip(addresses, durations), 1):
                    point_id = routes.create_point(route_id, address, -19.93 + order * .005, -44.05 + order * .005, order)
                    departure = arrival + timedelta(minutes=minutes + days_ago)
                    if days_ago:
                        point = routes.find_point(point_id)
                        point.update(data_hora_chegada=arrival.astimezone(timezone.utc).isoformat(),
                                     data_hora_saida=departure.astimezone(timezone.utc).isoformat())
                        routes.update_point(point)
                    arrival = departure + timedelta(minutes=20)
                routes.update_status(route_id, 'concluido' if days_ago else 'planejado')
                service.recalculate(route_id)
    content = 'Dados fictícios. Senhas locais geradas aleatoriamente.\n' + '\n'.join(credentials) + '\n'
    credentials_path = database.path.parent / 'credenciais-demo.txt'
    with open(credentials_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o600)) as output:
        output.write(content)
    credentials_path.chmod(0o600)
    print(content, flush=True)
