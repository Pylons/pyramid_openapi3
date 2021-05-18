"""Test rendering errors as JSON responses."""

from openapi_core.unmarshalling.schemas.formatters import Formatter
from pyramid.config import Configurator
from pyramid.httpexceptions import exception_response
from pyramid.router import Router
from pyramid_openapi3.exceptions import InvalidCustomFormatterValue
from pyramid_openapi3.exceptions import RequestValidationError
from webtest.app import TestApp

import openapi_core
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
          {endpoints}
    """

    def _testapp(self, view: t.Callable, endpoints: str, route="/foo") -> TestApp:
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(self.OPENAPI_YAML.format(endpoints=endpoints).encode())
            document.seek(0)

            return TestApp(app(document.name, view, route))

    def test_missing_query_parameter(self) -> None:
        """Render nice ValidationError if query parameter is missing."""
        endpoints = """
          /foo:
            post:
              parameters:
                - name: bar
                  in: query
                  required: true
                  schema:
                    type: integer
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(view=self.foo, endpoints=endpoints).post("/foo", status=400)
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            }
        ]

    def test_invalid_query_parameter(self) -> None:
        """Render nice ValidationError if query parameter is invalid."""
        endpoints = """
          "/foo":
            post:
              parameters:
                - name: bar
                  in: query
                  required: true
                  schema:
                    type: integer
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(view=self.foo, endpoints=endpoints).post("/foo", status=400)
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            }
        ]

    def test_invalid_path_parameter(self) -> None:
        """Render nice ValidationError if path parameter is invalid."""
        endpoints = """
          "/foo/{bar}":
            post:
              parameters:
                - name: bar
                  in: path
                  required: true
                  schema:
                    type: integer
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(
            view=self.foo, endpoints=endpoints, route="/foo/{bar}"
        ).post("/foo/bar", status=400)
        assert res.json == [
            {
                "exception": "CastError",
                "message": "Failed to cast value bar to type integer",
            }
        ]

    def test_invalid_path_parameter_regex(self) -> None:
        """Render nice ValidationError if path parameter does not match regex."""
        endpoints = """
          "/foo/{bar}":
            post:
              parameters:
                - name: bar
                  in: path
                  required: true
                  schema:
                    type: string
                    pattern: '^[0-9]{2}-[A-F]{4}$'
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(
            view=self.foo, endpoints=endpoints, route="/foo/{bar}"
        ).post("/foo/not-a-valid-uuid", status=400)
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "'not-a-valid-uuid' does not match '^[0-9]{2}-[A-F]{4}$'",
                # TODO: ideally, this response would include "field"
                # but I don't know how I can achieve this ATM ¯\_(ツ)_/¯
            }
        ]

    def test_invalid_path_parameter_uuid(self) -> None:
        """Render nice ValidationError if path parameter is not UUID."""
        endpoints = """
          "/foo/{bar}":
            post:
              parameters:
                - name: bar
                  in: path
                  required: true
                  schema:
                    type: string
                    format: uuid
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(
            view=self.foo, endpoints=endpoints, route="/foo/{bar}"
        ).post("/foo/not-a-valid-uuid", status=400)
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "'not-a-valid-uuid' is not a 'uuid'",
                # TODO: ideally, this response would include "field"
                # but I don't know how I can achieve this ATM ¯\_(ツ)_/¯
            }
        ]

    def test_missing_header_parameter(self) -> None:
        """Render nice ValidationError if header parameter is missing."""
        endpoints = """
          "/foo":
            post:
              parameters:
                - name: bar
                  in: header
                  required: true
                  schema:
                    type: integer
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(view=self.foo, endpoints=endpoints).post("/foo", status=400)
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            }
        ]

    def test_missing_cookie_parameter(self) -> None:
        """Render nice ValidationError if cookie parameter is missing."""
        endpoints = """
          "/foo":
            post:
              parameters:
                - name: bar
                  in: cookie
                  required: true
                  schema:
                    type: integer
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(view=self.foo, endpoints=endpoints).post("/foo", status=400)
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            }
        ]

    def test_missing_POST_parameter(self) -> None:
        """Render nice ValidationError if POST parameter is missing."""
        endpoints = """
          "/foo":
            post:
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
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(view=self.foo, endpoints=endpoints).post_json(
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
        endpoints = """
          "/foo":
            post:
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
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(view=self.foo, endpoints=endpoints).post_json(
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
        endpoints = """
          "/foo":
            post:
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
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """

        res = self._testapp(view=self.foo, endpoints=endpoints).post_json(
            "/foo", {"foo": "12"}, status=400
        )
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "'12' is too short",
                "field": "foo",
            }
        ]

    def test_multiple_errors(self) -> None:
        """Render a list of errors if there are more than one."""
        endpoints = """
          /foo:
            post:
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
                          minLength: 5
                          maxLength: 3
              parameters:
                - name: bar
                  in: query
                  required: true
                  schema:
                    type: string
                - name: bam
                  in: query
                  schema:
                    type: integer
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        """
        res = self._testapp(view=self.foo, endpoints=endpoints).post_json(
            "/foo?bam=abc", {"foo": "1234"}, status=400
        )
        assert res.json == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required parameter: bar",
                "field": "bar",
            },
            {
                "exception": "CastError",
                "message": "Failed to cast value abc to type integer",
            },
            {
                "exception": "ValidationError",
                "message": "'1234' is too short",
                "field": "foo",
            },
            {
                "exception": "ValidationError",
                "message": "'1234' is too long",
                "field": "foo",
            },
        ]

    def test_bad_JWT_token(self) -> None:
        """Render 401 on bad JWT token."""
        endpoints = """
          /foo:
            get:
              security:
                - Token:
                    []
              responses:
                200:
                  description: Say hello
                401:
                  description: Unauthorized
        components:
          securitySchemes:
            Token:
              type: apiKey
              name: Authorization
              in: header
        """
        res = self._testapp(view=self.foo, endpoints=endpoints).get("/foo", status=401)
        assert res.json == [
            {
                "exception": "InvalidSecurity",
                "message": "Security not valid for any requirement",
            }
        ]

    def test_lists(self) -> None:
        """Error extracting works for lists too."""
        endpoints = """
          /foo:
            post:
              requestBody:
                description: A list of bars
                content:
                  application/json:
                    schema:
                      required:
                        - foo
                      type: object
                      properties:
                        foo:
                          type: array
                          items:
                            $ref: "#/components/schemas/bar"
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
        components:
          schemas:
            bar:
              required:
                - bam
              type: object
              properties:
                bam:
                  type: number
        """
        res = self._testapp(view=self.foo, endpoints=endpoints).post_json(
            "/foo", {"foo": [{"bam": "not a number"}]}, status=400
        )

        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "'not a number' is not of type number",
                "field": "foo/0/bam",
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

            return TestApp(app(document.name, view, route="/foo"))

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
        if openapi_core.__version__ == "0.13.8":  # pragma: no cover
            assert res.json == [
                {
                    "exception": "ResponseNotFound",
                    "message": "Unknown response http status: 409",
                }
            ]
        else:  # pragma: no cover
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
            }
        ]


class CustomFormattersTests(unittest.TestCase):
    """A suite of tests that showcase how custom formatters can be used."""

    def hello(self, context, request) -> str:
        """Say hello."""
        return f"Hello {request.openapi_validated.body['name']}"

    class UniqueName(Formatter):  # noqa: D106
        def validate(self, name: str) -> str:
            """Ensure name is unique."""
            if not isinstance(name, str):
                return name

            name = name.lower()
            if name in ["alice", "bob"]:
                raise RequestValidationError(
                    errors=[
                        InvalidCustomFormatterValue(  # type: ignore
                            value=name,
                            type="unique-name",
                            original_exception=f"Name '{name}' already taken. Choose a different name!",
                            field="name",
                        )
                    ]
                )
            return name

    OPENAPI_YAML = """
        openapi: "3.0.0"
        info:
          version: "1.0.0"
          title: Foo
        paths:
          /hello:
            post:
              requestBody:
                required: true
                content:
                  application/json:
                    schema:
                      type: object
                      required:
                        - name
                      properties:
                        name:
                          type: string
                          minLength: 3
                          format: unique-name
              responses:
                200:
                  description: Say hello
                400:
                  description: Bad Request
    """

    def _testapp(self) -> TestApp:
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(self.OPENAPI_YAML.encode())
            document.seek(0)

            with Configurator() as config:
                config.include("pyramid_openapi3")
                config.pyramid_openapi3_spec(document.name)
                config.pyramid_openapi3_add_formatter("unique-name", self.UniqueName())
                config.add_route("hello", "/hello")
                config.add_view(
                    openapi=True, renderer="json", view=self.hello, route_name="hello"
                )
                app = config.make_wsgi_app()

            return TestApp(app)

    def test_say_hello(self) -> None:
        """Test happy path."""
        res = self._testapp().post_json("/hello", {"name": "zupo"}, status=200)
        assert res.json == "Hello zupo"

    def test_name_taken(self) -> None:
        """Test passing a name that is taken."""
        res = self._testapp().post_json("/hello", {"name": "Alice"}, status=400)
        assert res.json == [
            {
                "exception": "InvalidCustomFormatterValue",
                "field": "name",
                "message": "Name 'alice' already taken. Choose a different name!",
            }
        ]

    def test_invalid_name(self) -> None:
        """Test that built-in type formatters do their job."""
        res = self._testapp().post_json("/hello", {"name": 12}, status=400)
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "12 is not of type string",
                "field": "name",
            }
        ]

        res = self._testapp().post_json("/hello", {"name": "yo"}, status=400)
        assert res.json == [
            {
                "exception": "ValidationError",
                "message": "'yo' is too short",
                "field": "name",
            }
        ]
