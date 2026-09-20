from ..response import Response


class TeamController:
    def __init__(self, team, service):
        self.team = team
        self.service = service

    def list_people(self, request):
        return Response(self.team.list_people(request.user))

    def create_driver(self, request):
        return Response(self.service.create_person(request.user, request.data, 'motorista'), status=201)

    def create_manager(self, request):
        return Response(self.service.create_person(request.user, request.data, 'gerente'), status=201)
