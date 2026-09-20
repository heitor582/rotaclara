from .controllers.audit_controller import AuditController
from .controllers.authentication_controller import AuthenticationController
from .controllers.parameter_controller import ParameterController
from .controllers.report_controller import ReportController
from .controllers.route_controller import RouteController
from .controllers.team_controller import TeamController
from .endpoints import define_endpoints
from .repositories.account_repository import AccountRepository
from .repositories.audit_repository import AuditRepository
from .repositories.parameter_repository import ParameterRepository
from .repositories.report_repository import ReportRepository
from .repositories.route_repository import RouteRepository
from .repositories.team_repository import TeamRepository
from .services.authentication_service import AuthenticationService
from .services.parameter_service import ParameterService
from .services.report_service import ReportService
from .services.route_service import RouteService
from .services.team_service import TeamService


def build_request_dependencies(connection, clock, login_limiter, secure_cookie):
    accounts = AccountRepository(connection)
    team = TeamRepository(connection)
    parameters = ParameterRepository(connection)
    audit = AuditRepository(connection)
    authentication = AuthenticationService(accounts, login_limiter, clock)
    route_service = RouteService(RouteRepository(connection), team, parameters, audit, clock)
    endpoints = define_endpoints(
        authentication=AuthenticationController(authentication, secure_cookie),
        team=TeamController(team, TeamService(team, accounts)),
        parameters=ParameterController(parameters, ParameterService(parameters, audit, clock)),
        routes=RouteController(route_service),
        reports=ReportController(ReportService(ReportRepository(connection), clock)),
        audit=AuditController(audit),
    )
    return authentication, endpoints
