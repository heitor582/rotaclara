from .endpoint import Endpoint


def define_endpoints(authentication, team, parameters, routes, reports, audit):
    return (
        Endpoint('POST', r'/api/login', authentication.login, requires_authentication=False),
        Endpoint('GET', r'/api/me', authentication.current_user),
        Endpoint('POST', r'/api/logout', authentication.logout),
        Endpoint('GET', r'/api/pessoas', team.list_people),
        Endpoint('POST', r'/api/motoristas', team.create_driver),
        Endpoint('POST', r'/api/gerentes', team.create_manager),
        Endpoint('GET', r'/api/parametros', parameters.get),
        Endpoint('PUT', r'/api/parametros', parameters.update),
        Endpoint('POST', r'/api/roteiros', routes.create),
        Endpoint('POST', r'/api/roteiros/(?P<route_id>\d+)/iniciar', routes.start),
        Endpoint('POST', r'/api/pontos/(?P<point_id>\d+)', routes.record_visit),
        Endpoint('PUT', r'/api/pontos/(?P<point_id>\d+)', routes.correct_point),
        Endpoint('GET', r'/api/relatorio', reports.get),
        Endpoint('GET', r'/api/exportar\.csv', reports.export_csv),
        Endpoint('GET', r'/api/auditoria', audit.list_entries),
    )


def resolve_endpoint(endpoints, method, path):
    for endpoint in endpoints:
        parameters = endpoint.match(method, path)
        if parameters is not None:
            return endpoint, parameters
    return None, {}
