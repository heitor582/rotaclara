def route_scope(user):
    if user['perfil'] == 'administrador':
        return '1=1', []
    if user['perfil'] == 'motorista':
        return 'r.motorista_id=?', [user['motorista_id']]
    if user['perfil'] == 'gerente':
        return 'r.motorista_id IN (SELECT id FROM motorista WHERE gerente_id=?)', [user['gerente_id']]
    raise PermissionError('Perfil inválido.')
