from ..domain import MANAGEMENT_ROLES, require_roles, validate_number

class ParameterService:
    def __init__(self, parameters, audit, clock):
        self.parameters = parameters
        self.audit = audit
        self.clock = clock

    def update(self, user, data):
        require_roles(user, *MANAGEMENT_ROLES)
        fuel_price = validate_number(data.get('valor_combustivel'), 'Combustível')
        efficiency = validate_number(data.get('km_por_litro'), 'Rendimento', .01)
        hours = validate_number(data.get('jornada_padrao_horas'), 'Jornada', .01, 24)
        before = self.parameters.get()
        self.parameters.update(fuel_price, efficiency, hours)
        self.audit.record(user, None, 'parametros', before, self.parameters.get(),
                          'Configuração para novos roteiros', self.clock.timestamp())
