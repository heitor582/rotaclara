from .base import Repository

class TeamRepository(Repository):
    def find_driver(self, driver_id):
        return self.one('SELECT * FROM motorista WHERE id=?', (driver_id,))

    def list_people(self, user):
        if user['perfil'] == 'administrador':
            drivers = self.all('SELECT * FROM motorista ORDER BY nome')
            managers = self.all('SELECT * FROM gerente ORDER BY nome')
        elif user['perfil'] == 'gerente':
            drivers = self.all('SELECT * FROM motorista WHERE gerente_id=? ORDER BY nome', (user['gerente_id'],))
            managers = self.all('SELECT * FROM gerente WHERE id=?', (user['gerente_id'],))
        else:
            drivers = self.all('SELECT id,nome,veiculo,km_por_litro FROM motorista WHERE id=?', (user['motorista_id'],))
            managers = []
        return {'motoristas': drivers, 'gerentes': managers}

    def create_driver(self, manager_id, name, phone, document, vehicle, efficiency):
        return self.connection.execute('INSERT INTO motorista(gerente_id,nome,telefone,documento,veiculo,km_por_litro) '
                                       'VALUES (?,?,?,?,?,?)', (manager_id, name, phone, document, vehicle, efficiency)).lastrowid

    def create_manager(self, name, phone, email):
        return self.connection.execute('INSERT INTO gerente(nome,telefone,email) VALUES (?,?,?)',
                                       (name, phone, email)).lastrowid
