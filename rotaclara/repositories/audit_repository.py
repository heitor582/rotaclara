import json

from .base import Repository
from .scope import route_scope

class AuditRepository(Repository):
    def record(self, user, point_id, action, before, after, reason, timestamp):
        self.connection.execute('INSERT INTO auditoria(usuario_id,instante,ponto_id,acao,antes,depois,motivo) '
                                'VALUES (?,?,?,?,?,?,?)', (user['id'], timestamp, point_id, action,
                                 json.dumps(before, ensure_ascii=False), json.dumps(after, ensure_ascii=False), reason))

    def list_accessible(self, user):
        condition, parameters = route_scope(user)
        return self.all('SELECT a.*,u.login FROM auditoria a JOIN usuario u ON u.id=a.usuario_id '
                        'LEFT JOIN ponto p ON p.id=a.ponto_id LEFT JOIN roteiro r ON r.id=p.roteiro_id '
                        f'WHERE {condition} ORDER BY a.id DESC LIMIT 500', parameters)
