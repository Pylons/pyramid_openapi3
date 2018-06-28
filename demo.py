import random

from pyramid.config import Configurator
from pyramid.view import view_config, exception_view_config

from wsgiref.simple_server import make_server


@view_config(route_name="pets", renderer="json", request_method="GET")
def pets_get(request):
    return {}

@view_config(route_name="pets", renderer="json", request_method="POST")
def pets_post(request):
    return {}

@view_config(route_name="a_pet", request_method="GET", renderer="json")
def apet(request):
    return {
        "a_field": random.random(),
        "b_field": random.randint(1, 999999),
    }

if __name__ == "__main__":
    with Configurator() as config:
        config.add_route("pets", "/pets")
        config.add_route("a_pet", "/pets/{petId}")

        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec('demo.yaml')
        config.pyramid_openapi3_add_explorer()
        config.scan(".")
        app = config.make_wsgi_app()

    print("visit api explorer at http://0.0.0.0:6543/docs/")
    server = make_server("0.0.0.0", 6543, app)
    server.serve_forever()
