from .base import Repository

class AccountRepository(Repository):
    def find_by_login(self, login):
        return self.one('SELECT * FROM usuario WHERE login=?', (login,))

    def find_session_user(self, token_hash, current_time):
        return self.one('SELECT u.* FROM sessao s JOIN usuario u ON u.id=s.usuario_id '
                        'WHERE s.token_hash=? AND s.expira>?', (token_hash, current_time))

    def create_session(self, token_hash, user_id, expires, current_time):
        self.connection.execute('DELETE FROM sessao WHERE expira<?', (current_time,))
        self.connection.execute('INSERT INTO sessao VALUES (?,?,?)', (token_hash, user_id, expires))

    def delete_session(self, token_hash):
        self.connection.execute('DELETE FROM sessao WHERE token_hash=?', (token_hash,))

    def create_account(self, login, password_hash, role, driver_id=None, manager_id=None):
        self.connection.execute('INSERT INTO usuario(login,senha_hash,perfil,motorista_id,gerente_id) '
                                'VALUES (?,?,?,?,?)', (login, password_hash, role, driver_id, manager_id))
