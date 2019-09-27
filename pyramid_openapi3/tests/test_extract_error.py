"""Test rendering errors as JSON responses."""

from pyramid.config import Configurator
from pyramid.httpexceptions import exception_response
from pyramid.router import Router
from webtest.app import TestApp

import tempfile
import typing as t
import unittest


def app(spec: str, view: t.Callable) -> Router:
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.pyramid_openapi3_JSONify_errors()
        config.add_route("foo", "/foo")
        config.add_view(openapi=True, renderer="json", view=view, route_name="foo")
        return config.make_wsgi_app()


class BadRequestsTests(unittest.TestCase):
    """A suite of tests that make sure bad requests are handled."""

    def foo(*args) -> None:  # noqa: D102
        return None  # pragma: no cover

    OPENAPI_YAML = """
        openapi: "3.0.0"
        info:
          version: "1.0.0"
          title: Foo
        paths:
          /foo:
            post:
              {parameters}
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
    """

    def _testapp(self, view: t.Callable, parameters: str) -> TestApp:
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(self.OPENAPI_YAML.format(parameters=parameters).encode())
            document.seek(0)

            return TestApp(app(document.name, view))

    def test_missing_path_parameter(self) -> None:
        """Render nice ValidationError if path parameter is missing."""

        parameters = """
              parameters:
                - name: bar
                  in: query
                  required: true
                  schema:
                    type: integer
        """

        res = self._testapp(view=self.foo, parameters=parameters).post(
            "/foo", status=400
        )
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            }
        ]

    def test_missing_header_parameter(self) -> None:
        """Render nice ValidationError if header parameter is missing."""

        parameters = """
              parameters:
                - name: bar
                  in: header
                  required: true
                  schema:
                    type: integer
        """

        res = self._testapp(view=self.foo, parameters=parameters).post(
            "/foo", status=400
        )
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            }
        ]

    def test_missing_cookie_parameter(self) -> None:
        """Render nice ValidationError if cookie parameter is missing."""

        parameters = """
              parameters:
                - name: bar
                  in: cookie
                  required: true
                  schema:
                    type: integer
        """

        res = self._testapp(view=self.foo, parameters=parameters).post(
            "/foo", status=400
        )
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            }
        ]

    def test_missing_POST_parameter(self) -> None:
        """Render nice ValidationError if POST parameter is missing."""

        parameters = """
              requestBody:
                required: true
                description: Data for saying foo
                content:
                  application/json:
                    schema:
                      type: object
                      required:
                        - foo
                      properties:
                        foo:
                          type: string
        """

        res = self._testapp(view=self.foo, parameters=parameters).post_json(
            "/foo", {}, status=400
        )
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "'foo' is a required property",
                "field": "foo",
            }
        ]

    def test_missing_type_POST_parameter(self) -> None:
        """Render nice ValidationError if POST parameter is of invalid type."""

        parameters = """
              requestBody:
                required: true
                description: Data for saying foo
                content:
                  application/json:
                    schema:
                      type: object
                      required:
                        - foo
                      properties:
                        foo:
                          type: string
        """

        res = self._testapp(view=self.foo, parameters=parameters).post_json(
            "/foo", {"foo": 1}, status=400
        )
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "1 is not of type string",
                "field": "foo",
            }
        ]

    def test_invalid_length_POST_parameter(self) -> None:
        """Render nice ValidationError if POST parameter is of invalid length."""
        parameters = """
              requestBody:
                required: true
                description: Data for saying foo
                content:
                  application/json:
                    schema:
                      type: object
                      properties:
                        foo:
                          type: string
                          minLength: 3
        """

        res = self._testapp(view=self.foo, parameters=parameters).post_json(
            "/foo", {"foo": "12"}, status=400
        )
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "'12' is too short",
                "field": "foo",
            }
        ]


class BadResponsesTests(unittest.TestCase):
    """A suite of tests that make sure bad responses are prevented."""

    OPENAPI_YAML = b"""
        openapi: "3.0.0"
        info:
          version: "1.0.0"
          title: Foo
        paths:
          /foo:
            get:
              responses:
                200:
                  description: Say foo
                400:
                  description: Bad Request
                  content:
                    application/json:
                      schema:
                        type: string
    """

    def _testapp(self, view: t.Callable) -> TestApp:
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(self.OPENAPI_YAML)
            document.seek(0)

            return TestApp(app(document.name, view))

    def test_foo(self) -> None:
        """Say foo."""

        def foo(*args):
            """Say foobar."""
            return {"foo": "bar"}

        res = self._testapp(view=foo).get("/foo", status=200)
        self.assertIn('{"foo": "bar"}', res.text)

    def test_invalid_response_code(self) -> None:
        """Prevent responding with undefined response code."""

        def foo(*args):
            raise exception_response(409, json_body={})

        res = self._testapp(view=foo).get("/foo", status=500)
        assert res.json == [
            {
                "exception": "InvalidResponse",
                "message": "Unknown response http status: 409",
            }
        ]

    def test_invalid_response_schema(self) -> None:
        """Prevent responding with unmatching response schema."""
        from pyramid.httpexceptions import exception_response

        def foo(*args):
            raise exception_response(400, json_body={"foo": "bar"})

        res = self._testapp(view=foo).get("/foo", status=500)
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "{'foo': 'bar'} is not of type string",
                "field": "type",
            }
        ]
