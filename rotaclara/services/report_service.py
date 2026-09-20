from ..domain import calculate_journey_percentage
from ..report_filters import ReportFilters

class ReportService:
    def __init__(self, reports, clock):
        self.reports = reports
        self.clock = clock

    def generate(self, user, query):
        filters = ReportFilters.from_query(query, self.clock.today())
        routes, points = self.reports.list_records(user, filters)
        if filters.search:
            points = [point for point in points if filters.search in point['endereco'].casefold()
                      or filters.search in point['motorista'].casefold()]
        days = {}
        for route in routes:
            day = days.setdefault(route['data'], {'data': route['data'], 'minutos': 0, 'jornada': 0})
            day['minutos'] += route['tempo_total_parado']
            day['jornada'] += route['jornada_padrao_horas'] * 60
        total_minutes = sum(route['tempo_total_parado'] for route in routes)
        journey_minutes = sum(route['jornada_padrao_horas'] * 60 for route in routes)
        return {'inicio': filters.start, 'fim': filters.end, 'roteiros': routes, 'pontos': points,
                'dias': list(days.values()), 'total_minutos': total_minutes,
                'custo': sum(route['custo_estimado'] for route in routes),
                'percentual': calculate_journey_percentage(total_minutes, journey_minutes / 60) if journey_minutes else 0,
                'base_minutos': journey_minutes, 'distancia': sum(route['distancia_total'] for route in routes)}
