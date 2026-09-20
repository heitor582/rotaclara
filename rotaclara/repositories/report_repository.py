from .base import Repository
from .scope import route_scope

class ReportRepository(Repository):
    def list_records(self, user, filters):
        condition, parameters = route_scope(user)
        if filters.driver_id:
            condition += ' AND r.motorista_id=?'
            parameters.append(filters.driver_id)
        if filters.status == 'pendencias':
            condition += " AND r.status IN ('planejado','em_andamento')"
        elif filters.status:
            condition += ' AND r.status=?'
            parameters.append(filters.status)
        condition += ' AND r.data BETWEEN ? AND ?'
        parameters.extend([filters.start, filters.end])
        routes = self.all('SELECT r.*,m.nome motorista FROM roteiro r JOIN motorista m ON m.id=r.motorista_id '
                          f'WHERE {condition} ORDER BY r.data,r.id', parameters)
        points = self.all('SELECT p.*,r.data,m.nome motorista,r.motorista_id FROM ponto p '
                          'JOIN roteiro r ON r.id=p.roteiro_id JOIN motorista m ON m.id=r.motorista_id '
                          f'WHERE {condition} ORDER BY r.data,p.roteiro_id,p.ordem_sequencial', parameters)
        return routes, points
