from ..response import Response


class ParameterController:
    def __init__(self, parameters, service):
        self.parameters = parameters
        self.service = service

    def get(self, request):
        return Response(self.parameters.get())

    def update(self, request):
        self.service.update(request.user, request.data)
        return Response({'ok': True})
