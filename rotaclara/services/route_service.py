from ..domain import (LOCAL_TIMEZONE, MANAGEMENT_ROLES, authorize_driver, calculate_fuel_cost,
                      calculate_route_minutes, calculate_stop_minutes, parse_date, parse_timestamp,
                      require_roles, require_text, validate_number)

class RouteService:
    def __init__(self, routes, team, parameters, audit, clock):
        self.routes = routes
        self.team = team
        self.parameters = parameters
        self.audit = audit
        self.clock = clock

    def require_route(self, user, route_id):
        route = self.routes.find_accessible(user, route_id)
        if not route:
            raise PermissionError('Roteiro indisponível para este usuário.')
        return route

    def create(self, user, data):
        driver_id = user['motorista_id'] if user['perfil'] == 'motorista' else int(data['motorista_id'])
        driver = self.team.find_driver(driver_id)
        authorize_driver(user, driver)
        day = parse_date(data.get('data'))
        distance = validate_number(data.get('distancia_total'), 'Distância')
        points = data.get('pontos', [])
        if not isinstance(points, list) or not 2 <= len(points) <= 100:
            raise ValueError('O roteiro precisa de 2 a 100 pontos ordenados.')
        normalized_points = [self.validate_address(point) for point in points]
        route_id = self.routes.create(day, driver_id, distance, self.parameters.get(), driver['km_por_litro'])
        for order, point in enumerate(normalized_points, 1):
            point_id = self.routes.create_point(route_id, point['endereco'], point['latitude'], point['longitude'], order)
            self.audit.record(user, point_id, 'criacao', {}, point, 'Montagem do roteiro', self.clock.timestamp())
        self.recalculate(route_id)
        return {'id': route_id}

    def start(self, user, route_id):
        route = self.require_route(user, route_id)
        if route['status'] != 'planejado':
            raise ValueError('Este roteiro já foi iniciado.')
        if route['data'] != self.clock.today():
            raise ValueError('Inicie o roteiro na data planejada.')
        self.routes.update_status(route_id, 'em_andamento')

    def record_visit(self, user, point_id, action):
        point, route = self.get_accessible_point(user, point_id)
        if route['status'] != 'em_andamento':
            raise ValueError('Inicie o roteiro antes de registrar pontos.')
        if action not in ('chegada', 'saida'):
            raise ValueError('Ação inválida.')
        field = 'data_hora_' + action
        if point[field]:
            raise ValueError('Registro já realizado. Use a correção auditada.')
        if self.routes.has_pending_points(route['id'], point['ordem_sequencial']):
            raise ValueError('Conclua o ponto anterior antes de continuar.')
        updated = {**point, field: self.clock.timestamp()}
        self.save_point(user, route, point, updated, action, 'Coleta pelo relógio do servidor')

    def correct_point(self, user, point_id, data):
        require_roles(user, *MANAGEMENT_ROLES)
        point, route = self.get_accessible_point(user, point_id)
        reason = require_text(data, 'motivo', 500)
        updated = {**point, **self.validate_address(data)}
        for field in ('data_hora_chegada', 'data_hora_saida'):
            timestamp = parse_timestamp(data.get(field))
            updated[field] = timestamp.isoformat(timespec='seconds') if timestamp else None
        self.save_point(user, route, point, updated, 'correcao', reason)

    def get_accessible_point(self, user, point_id):
        point = self.routes.find_point(point_id)
        if not point:
            raise ValueError('Ponto não encontrado.')
        return point, self.require_route(user, point['roteiro_id'])

    @staticmethod
    def validate_address(data):
        if not isinstance(data, dict):
            raise ValueError('Informe um ponto válido.')
        return {'endereco': require_text(data, 'endereco'),
                'latitude': validate_number(data.get('latitude'), 'Latitude', -90, 90),
                'longitude': validate_number(data.get('longitude'), 'Longitude', -180, 180)}

    def validate_chronology(self, route, point):
        arrival = parse_timestamp(point['data_hora_chegada'])
        departure = parse_timestamp(point['data_hora_saida'])
        if arrival and arrival.astimezone(LOCAL_TIMEZONE).date().isoformat() != route['data']:
            raise ValueError('A chegada deve estar na data do roteiro.')
        current_time = self.clock.now()
        if (arrival and arrival > current_time) or (departure and departure > current_time):
            raise ValueError('Não é permitido registrar horários futuros.')
        previous = self.routes.find_neighbor(route['id'], point['ordem_sequencial'] - 1)
        following = self.routes.find_neighbor(route['id'], point['ordem_sequencial'] + 1)
        if arrival and previous and (not previous['data_hora_saida'] or arrival < parse_timestamp(previous['data_hora_saida'])):
            raise ValueError('A chegada deve ocorrer após a saída do ponto anterior.')
        if following and following['data_hora_chegada'] and (not departure or departure > parse_timestamp(following['data_hora_chegada'])):
            raise ValueError('A saída deve ocorrer antes da chegada ao próximo ponto.')

    def save_point(self, user, route, before, after, action, reason):
        after['tempo_parado_minutos'] = calculate_stop_minutes(after)
        self.validate_chronology(route, after)
        self.routes.update_point(after)
        self.audit.record(user, after['id'], action, before, after, reason, self.clock.timestamp())
        self.recalculate(route['id'])
        if not self.routes.has_pending_points(route['id']):
            status = 'concluido'
        elif route['status'] != 'planejado' or after['data_hora_chegada']:
            status = 'em_andamento'
        else:
            status = 'planejado'
        self.routes.update_status(route['id'], status)

    def recalculate(self, route_id):
        points = self.routes.list_points(route_id)
        for point in points:
            self.routes.update_point_minutes(point['id'], calculate_stop_minutes(point))
        route = self.routes.find(route_id)
        cost = calculate_fuel_cost(route['distancia_total'], route['valor_combustivel'], route['km_por_litro'])
        self.routes.update_totals(route_id, calculate_route_minutes(points), cost)
