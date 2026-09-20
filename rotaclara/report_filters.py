from dataclasses import dataclass

from .domain import parse_date

@dataclass(frozen=True)
class ReportFilters:
    start: str
    end: str
    driver_id: int | None = None
    status: str = ''
    search: str = ''

    @classmethod
    def from_query(cls, query, today):
        start = parse_date(query.get('inicio', [today])[0])
        end = parse_date(query.get('fim', [today])[0])
        if end < start:
            raise ValueError('Data final deve ser igual ou posterior à inicial.')
        status = query.get('status', [''])[0]
        if status not in ('', 'pendencias', 'planejado', 'em_andamento', 'concluido'):
            raise ValueError('Status inválido.')
        driver_id = query.get('motorista', [''])[0]
        return cls(start, end, int(driver_id) if driver_id else None, status,
                   query.get('busca', [''])[0].casefold().strip())
