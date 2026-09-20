from ..response import Response


class RouteController:
    def __init__(self, service):
        self.service = service

    def create(self, request):
        return Response(self.service.create(request.user, request.data), status=201)

    def start(self, request, route_id):
        self.service.start(request.user, route_id)
        return Response({'ok': True})

    def record_visit(self, request, point_id):
        self.service.record_visit(request.user, point_id, request.data.get('acao'))
        return Response({'ok': True})

    def correct_point(self, request, point_id):
        self.service.correct_point(request.user, point_id, request.data)
        return Response({'ok': True})
