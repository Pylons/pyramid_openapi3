"""A single-file demo of pyramid_openapi3.

See README.md at
https://github.com/Pylons/pyramid_openapi3/tree/master/examples/singlefile
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
    components:
      schemas:
        ObjectWithName:
          type: object
          properties:
            name:
              type: string
          required:
            - name
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
            400:
              description: Bad Request
        post:
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/ObjectWithName"
              application/x-www-form-urlencoded:
                schema:
                  $ref: "#/components/schemas/ObjectWithName"
          responses:
            200:
              description: Say hello
            400:
              description: Bad Request
"""


@view_config(
    route_name="hello", renderer="json", request_method=("GET", "POST"), openapi=True
)
def hello(request):
    """Say hello."""
    # This implementation is a bit weird, but I could only get webtest to work if there was a
    # single view function handling the route.
    if request.method == "POST":
        return {"hello_post": request.openapi_validated.body["name"]}

    if request.openapi_validated.parameters["query"]["name"] == "admin":
        raise HTTPForbidden()
    return {"hello": request.openapi_validated.parameters["query"]["name"]}


def app(spec):
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.pyramid_openapi3_add_explorer()

        # This is a workaround for the issue:
        #
        # from urllib.parse import parse_qsl
        #
        # config.pyramid_openapi3_add_deserializer(
        #     "application/x-www-form-urlencoded",
        #     lambda body_bytes: dict(parse_qsl(body_bytes.decode(encoding="ascii"))),
        # )

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

    def test_hello_post_json(self):
        """Say hello to a json POST."""
        res = self.testapp.post_json("/hello", {"name": "jane"}, status=200)
        self.assertIn('{"hello_post": "jane"}', res.text)

    def test_hello_post_form(self):
        """Say hello to a form POST."""
        # Make the request but don't assert the status immediately
        res = self.testapp.post("/hello", params={"name": "joe"}, status="*")
        # First (and for our own sanity) assert the request is actually what we expect it to be
        self.assertEqual(
            "POST /hello HTTP/1.0\r\n"
            "Content-Length: 8\r\n"
            "Content-Type: application/x-www-form-urlencoded\r\n"
            "Host: localhost:80\r\n"
            "\r\n"
            "name=joe",
            str(res.request),
        )
        # Then assert the status, this fails, status_code is 400
        self.assertEqual(200, res.status_code)
        # And this also fails, response text is:
        #   [
        #     {
        #       "exception": "ValidationError",
        #       "message": "'name' is a required property",
        #       "field": "name"
        #     }
        #   ]
        self.assertIn('{"hello_post": "joe"}', res.text)

    def test_undefined_response(self):
        """Saying hello to admin should fail with 403 Forbidden.

        But because we have not defined how a 403 response should look in
        OPENAPI_DOCUMENT, we instead get an error 500 response, because it is
        the servers fault to generate an invalid response.

        This is to prevent us from forgetting to define all possible responses
        in our openapi document.
        """
        res = self.testapp.get("/hello?name=admin", status=500)
        self.assertIn("Unknown response http status: 403", res.text)

    def test_name_missing(self):
        """Our view code does not even get called is request is not per-spec.

        We don't have to write (and test!) any validation code in our view!
        """
        res = self.testapp.get("/hello", status=400)
        self.assertIn("Missing required parameter: name", res.text)

    def test_name_too_short(self):
        """A name that is too short is picked up by openapi-core validation.

        We don't have to write (and test!) any validation code in our view!
        """
        res = self.testapp.get("/hello?name=yo", status=400)
        self.assertIn("'yo' is too short", res.text)
