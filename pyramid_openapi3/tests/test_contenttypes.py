"""Test different request body content types."""

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.router import Router
from webtest.app import TestApp

import tempfile
import typing as t
import unittest


def app(spec: str, view: t.Callable, route: str) -> Router:
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.add_route("foo", route)
        config.add_view(openapi=True, renderer="json", view=view, route_name="foo")
        return config.make_wsgi_app()


OPENAPI_YAML = """
    openapi: "3.0.0"
    info:
      version: "1.0.0"
      title: Foo
    components:
      schemas:
        ObjectWithName:
          type: object
          properties:
            bar:
              type: string
    paths:
      /foo:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/ObjectWithName"
              application/x-www-form-urlencoded:
                schema:
                  $ref: "#/components/schemas/ObjectWithName"
              multipart/form-data:
                schema:
                  $ref: "#/components/schemas/ObjectWithName"
          responses:
            200:
              description: OK
            400:
              description: Bad Request
"""


class TestContentTypes(unittest.TestCase):
    """A suite of tests that make sure different body content types are supported."""

    def _testapp(self) -> TestApp:
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        def foo_view(request: Request) -> t.Dict[str, str]:
            """Return reversed string."""
            return {"bar": request.openapi_validated.body["bar"][::-1]}

        with tempfile.NamedTemporaryFile() as document:
            document.write(OPENAPI_YAML.encode())
            document.seek(0)

            return TestApp(app(document.name, foo_view, "/foo"))

    def test_post_json(self) -> None:
        """Post with `application/json`."""

        res = self._testapp().post_json("/foo", {"bar": "baz"}, status=200)
        self.assertEqual(res.json, {"bar": "zab"})

    def test_post_form(self) -> None:
        """Post with `application/x-www-form-urlencoded`."""

        res = self._testapp().post("/foo", params={"bar": "baz"}, status=200)
        self.assertEqual(res.json, {"bar": "zab"})

    def test_post_form_multipart(self) -> None:
        """Post with `multipart/form-data`."""

        res = self._testapp().post(
            "/foo",
            params={"bar": "baz"},
            content_type="multipart/form-data",
            status=200,
        )
        self.assertEqual(res.json, {"bar": "zab"})
