from .base import Repository

class ParameterRepository(Repository):
    def get(self):
        return self.one('SELECT * FROM parametro WHERE id=1')

    def update(self, fuel_price, efficiency, hours):
        self.connection.execute('UPDATE parametro SET valor_combustivel=?,km_por_litro=?,custo_por_km=?, '
                                'jornada_padrao_horas=? WHERE id=1', (fuel_price, efficiency, fuel_price / efficiency, hours))
