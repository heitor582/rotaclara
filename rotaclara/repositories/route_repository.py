from .base import Repository
from .scope import route_scope

class RouteRepository(Repository):
    def find_accessible(self, user, route_id):
        condition, parameters = route_scope(user)
        return self.one(f'SELECT r.* FROM roteiro r WHERE r.id=? AND {condition}', [route_id] + parameters)

    def find(self, route_id):
        return self.one('SELECT * FROM roteiro WHERE id=?', (route_id,))

    def list_points(self, route_id):
        return self.all('SELECT * FROM ponto WHERE roteiro_id=? ORDER BY ordem_sequencial', (route_id,))

    def find_point(self, point_id):
        return self.one('SELECT * FROM ponto WHERE id=?', (point_id,))

    def find_neighbor(self, route_id, order):
        return self.one('SELECT * FROM ponto WHERE roteiro_id=? AND ordem_sequencial=?', (route_id, order))

    def has_pending_points(self, route_id, before_order=None):
        sql = 'SELECT id FROM ponto WHERE roteiro_id=? AND data_hora_saida IS NULL'
        parameters = [route_id]
        if before_order is not None:
            sql += ' AND ordem_sequencial<?'
            parameters.append(before_order)
        return self.one(sql + ' LIMIT 1', parameters) is not None

    def create(self, day, driver_id, distance, parameters, efficiency):
        return self.connection.execute('INSERT INTO roteiro(data,motorista_id,distancia_total,valor_combustivel, '
                                       'km_por_litro,custo_por_km,jornada_padrao_horas) VALUES (?,?,?,?,?,?,?)',
                                       (day, driver_id, distance, parameters['valor_combustivel'], efficiency,
                                        parameters['valor_combustivel'] / efficiency, parameters['jornada_padrao_horas'])).lastrowid

    def create_point(self, route_id, address, latitude, longitude, order):
        return self.connection.execute('INSERT INTO ponto(roteiro_id,endereco,latitude,longitude,ordem_sequencial) '
                                       'VALUES (?,?,?,?,?)', (route_id, address, latitude, longitude, order)).lastrowid

    def update_point(self, point):
        fields = ('endereco', 'latitude', 'longitude', 'data_hora_chegada', 'data_hora_saida', 'tempo_parado_minutos')
        assignments = ','.join(field + '=?' for field in fields)
        self.connection.execute(f'UPDATE ponto SET {assignments} WHERE id=?',
                                [point[field] for field in fields] + [point['id']])

    def update_point_minutes(self, point_id, minutes):
        self.connection.execute('UPDATE ponto SET tempo_parado_minutos=? WHERE id=?', (minutes, point_id))

    def update_totals(self, route_id, minutes, cost):
        self.connection.execute('UPDATE roteiro SET tempo_total_parado=?,custo_estimado=? WHERE id=?',
                                (minutes, cost, route_id))

    def update_status(self, route_id, status):
        self.connection.execute('UPDATE roteiro SET status=? WHERE id=?', (status, route_id))
