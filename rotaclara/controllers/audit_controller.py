from ..domain import MANAGEMENT_ROLES, require_roles
from ..response import Response


class AuditController:
    def __init__(self, audit):
        self.audit = audit

    def list_entries(self, request):
        require_roles(request.user, *MANAGEMENT_ROLES)
        return Response(self.audit.list_accessible(request.user))
