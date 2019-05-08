"""A single-file demo of pyramid_openapi3.

Usage:
* git clone https://github.com/Pylons/pyramid_openapi3.git
* cd pyramid_openapi3/examples/singlefile
* virtualenv -p python3.7 .
* source bin/activate
* pip install pyramid_openapi3
* python app.py
"""

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import view_config
from wsgiref.simple_server import make_server

import tempfile
import unittest

# This is usually in a separate openapi.yaml file, but for the sake of the
# example we want everything in a single file. Other examples have it nicely
# separated.
OPENAPI_DOCUMENT = b"""
    openapi: "3.0.0"
    info:
      version: "1.0.0"
      title: Hello API
    paths:
      /hello:
        get:
          parameters:
            - name: name
              in: query
              required: true
              schema:
                type: string
                minLength: 3
          responses:
            200:
              description: Say hello
"""


@view_config(route_name="hello", renderer="json", request_method="GET", openapi=True)
def hello(request):
    """Say hello."""
    if request.openapi_validated.parameters["query"]["name"] == "admin":
        raise HTTPForbidden()
    return {"hello": request.openapi_validated.parameters["query"]["name"]}


def app(spec):
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.pyramid_openapi3_add_explorer()
        config.add_route("hello", "/hello")
        config.scan(".")
        return config.make_wsgi_app()


if __name__ == "__main__":
    """If app.py is called directly, start up the app."""
    with tempfile.NamedTemporaryFile() as document:
        document.write(OPENAPI_DOCUMENT)
        document.seek(0)

        print("visit api explorer at http://0.0.0.0:6543/docs/")  # noqa: T001
        server = make_server("0.0.0.0", 6543, app(document.name))
        server.serve_forever()


#######################################
#           ---- Tests ----           #
# A couple of functional tests to     #
# showcase pyramid_openapi3 features. #
# Usage: python -m unittest app.py    #
#######################################

from openapi_core.schema.parameters.exceptions import InvalidParameterValue  # noqa
from openapi_core.schema.parameters.exceptions import MissingRequiredParameter  # noqa
from openapi_core.schema.responses.exceptions import InvalidResponse  # noqa


class FunctionalTests(unittest.TestCase):
    """A suite of tests that make actual requests to a running app."""

    def setUp(self):
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(OPENAPI_DOCUMENT)
            document.seek(0)

            self.testapp = TestApp(app(document.name))

    def test_nothing_on_root(self):
        """We have not configured our app to serve anything on root."""
        res = self.testapp.get("/", status=404)
        self.assertIn("404 Not Found", res.text)

    def test_api_explorer_on_docs(self):
        """Swagger's API Explorer should be served on /docs/."""
        res = self.testapp.get("/docs/", status=200)
        self.assertIn("<title>Swagger UI</title>", res.text)

    def test_hello(self):
        """Say hello."""
        res = self.testapp.get("/hello?name=john", status=200)
        self.assertIn('{"hello": "john"}', res.text)

    def test_undefined_response(self):
        """Saying hello to admin should fail with 403 Forbidden.

        But because we have not defined how a 403 response should look in
        OPENAPI_DOCUMENT, we instead get a InvalidResponse exception.

        This is to prevent us from forgetting to define all possible responses
        in our opeanapi document.
        """
        try:
            self.testapp.get("/hello?name=admin", status=200)
        except InvalidResponse as exc:
            self.assertEqual(str(exc), "Unknown response http status: 403")

    def test_name_missing(self):
        """Our view code does not even get called is request is not per-spec.

        We don't have to write (and test!) any validation code in our view!
        """
        try:
            self.testapp.get("/hello", status=200)
        except MissingRequiredParameter as exc:
            self.assertEqual(str(exc), "Missing required parameter: name")

    def test_name_too_short(self):
        """A name that is too short is picked up by openapi-core validation.

        We don't have to write (and test!) any validation code in our view!
        """
        try:
            self.testapp.get("/hello?name=yo", status=200)
        except InvalidParameterValue as exc:
            self.assertEqual(
                str(exc),
                "Invalid parameter value for `name`: Value is shorter (2) "
                "than the minimum length of 3",
            )
