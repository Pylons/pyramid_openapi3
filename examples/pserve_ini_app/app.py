import os
import sys

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.scripts.pserve import main
from pyramid.view import view_config

APP_FOLDER = os.path.dirname(__file__)


@view_config(route_name="version", renderer="json", request_method="GET", openapi=True)
def get(request: Request):
    """Get the app's version."""
    return {"Version": "0.0.1"}


def wsgi_app(global_config, **settings):
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(
            os.path.join(APP_FOLDER, "openapi.yaml")
        )
        config.pyramid_openapi3_add_explorer()
        config.add_route("version", "/version")
        config.scan(".")

        return config.make_wsgi_app()


if __name__ == '__main__':
    # The normal way of starting an app would be `pserve server.ini`
    # we replicate this here by adding a sys.argv

    # normally you'd have an egg or a proper package, but this app is simpler.
    # This way can only work when the working directory is the same as where app.py is
    # because of the hardcoded app:wsgi_app in server.ini
    os.chdir(APP_FOLDER)
    config_file = os.path.join(APP_FOLDER, 'server.ini')
    sys.argv.append(config_file)
    sys.exit(main())
