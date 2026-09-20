from ..exporters import export_points_csv
from ..response import Response


class ReportController:
    def __init__(self, service):
        self.service = service

    def get(self, request):
        return Response(self.service.generate(request.user, request.query))

    def export_csv(self, request):
        report = self.service.generate(request.user, request.query)
        return Response(export_points_csv(report['pontos']), content_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition': 'attachment; filename="rotaclara-relatorio.csv"'})
