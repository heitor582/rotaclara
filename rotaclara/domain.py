import math
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

LOCAL_TIMEZONE = ZoneInfo('America/Sao_Paulo')
MANAGEMENT_ROLES = ('administrador', 'gerente')


def validate_number(value, label, minimum=0, maximum=float('inf')):
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise ValueError(f'{label}: informe um número válido.') from None
    if isinstance(value, bool) or not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f'{label}: valor fora do intervalo permitido.')
    return number


def require_text(data, field, limit=200):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(f'{field}: preenchimento obrigatório (até {limit} caracteres).')
    return value.strip()


def require_password(data):
    password = data.get('senha')
    if not isinstance(password, str) or not 10 <= len(password) <= 200:
        raise ValueError('Use uma senha de 10 a 200 caracteres.')
    return password


def parse_date(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        raise ValueError('Data inválida.') from None


def parse_timestamp(value):
    if value is None or value == '':
        return None
    try:
        timestamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise ValueError('Horário inválido.') from None
    if timestamp.tzinfo is None:
        raise ValueError('Horário deve incluir fuso horário.')
    return timestamp.astimezone(timezone.utc)


def calculate_stop_minutes(point, order=None):
    order = point['ordem_sequencial'] if order is None else order
    arrival = parse_timestamp(point.get('data_hora_chegada'))
    departure = parse_timestamp(point.get('data_hora_saida'))
    if departure and not arrival:
        raise ValueError('Registre a chegada antes da saída.')
    if arrival and departure and departure < arrival:
        raise ValueError('A saída não pode ser anterior à chegada.')
    if order == 1 or not arrival or not departure:
        return 0.0
    return (departure - arrival).total_seconds() / 60


def calculate_route_minutes(points):
    return sum(calculate_stop_minutes(point) for point in points)


def calculate_fuel_cost(distance, fuel_price, efficiency):
    return (validate_number(distance, 'Distância') * validate_number(fuel_price, 'Combustível')
            / validate_number(efficiency, 'Rendimento', 0.000001))


def calculate_journey_percentage(minutes, hours=8):
    return validate_number(minutes, 'Tempo') / (validate_number(hours, 'Jornada', 0.000001) * 60) * 100


def require_roles(user, *roles):
    if user['perfil'] not in roles:
        raise PermissionError('Seu perfil não permite esta ação.')


def authorize_driver(user, driver):
    allowed = driver and (
        user['perfil'] == 'administrador'
        or user['perfil'] == 'gerente' and driver['gerente_id'] == user['gerente_id']
        or user['perfil'] == 'motorista' and driver['id'] == user['motorista_id']
    )
    if not allowed:
        raise PermissionError('Motorista fora da sua equipe.')
