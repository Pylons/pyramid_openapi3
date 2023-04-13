"""A single-file demo of pyramid_openapi3.

See README.md at
https://github.com/Pylons/pyramid_openapi3/tree/main/examples/singlefile
"""

from pyramid.config import Configurator
from pyramid.view import view_config
from wsgiref.simple_server import make_server

import tempfile
import unittest

# This is usually in a separate openapi.yaml file, but for the sake of the
# example we want everything in a single file. Other examples have it nicely
# separated.
OPENAPI_DOCUMENT = b"""
    openapi: "3.1.0"
    info:
      version: "1.0.0"
      title: Hello API
    paths:
      /today:
        get:
          responses:
            200:
              description: Say hello
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      today:
                        type: [string, "null"]
                        format: date

"""


@view_config(route_name="today", renderer="json", request_method="GET", openapi=True)
def today(request):
    """Return today's date or None."""
    return {"today": None}


def app(spec):
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.pyramid_openapi3_add_explorer()
        config.add_route("today", "/today")
        config.scan(".")
        return config.make_wsgi_app()


if __name__ == "__main__":
    """If app.py is called directly, start up the app."""
    with tempfile.NamedTemporaryFile() as document:
        document.write(OPENAPI_DOCUMENT)
        document.seek(0)

        print("visit api explorer at http://0.0.0.0:6543/docs/")  # noqa: T201
        server = make_server("0.0.0.0", 6543, app(document.name))
        server.serve_forever()


#######################################
#           ---- Tests ----           #
# A couple of functional tests to     #
# showcase pyramid_openapi3 features. #
# Usage: python -m unittest app.py    #
#######################################


class FunctionalTests(unittest.TestCase):
    """A suite of tests that make actual requests to a running app."""

    def setUp(self):
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(OPENAPI_DOCUMENT)
            document.seek(0)

            self.testapp = TestApp(app(document.name))

    def test_today(self):
        """Say today."""
        res = self.testapp.get("/today", status=200)
        self.assertIn('{"today": null}', res.text)
