from ..domain import MANAGEMENT_ROLES, require_roles, require_text, require_password, validate_number
from ..security.passwords import hash_password

class TeamService:
    def __init__(self, team, accounts):
        self.team = team
        self.accounts = accounts

    def create_person(self, user, data, role):
        require_roles(user, *(MANAGEMENT_ROLES if role == 'motorista' else ('administrador',)))
        name = require_text(data, 'nome')
        phone = require_text(data, 'telefone', 30)
        login = require_text(data, 'login', 80)
        password = require_password(data)
        if role == 'motorista':
            manager_id = user['gerente_id'] if user['perfil'] == 'gerente' else int(data['gerente_id'])
            person_id = self.team.create_driver(manager_id, name, phone, require_text(data, 'documento', 40),
                                                require_text(data, 'veiculo', 100),
                                                validate_number(data.get('km_por_litro'), 'Rendimento', .01))
        else:
            email = require_text(data, 'email')
            if '@' not in email:
                raise ValueError('Informe um e-mail válido.')
            person_id = self.team.create_manager(name, phone, email)
        self.accounts.create_account(login, hash_password(password), role,
                                     driver_id=person_id if role == 'motorista' else None,
                                     manager_id=person_id if role == 'gerente' else None)
        return {'id': person_id}
