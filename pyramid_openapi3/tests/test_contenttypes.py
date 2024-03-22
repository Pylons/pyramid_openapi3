"""Test different request body content types."""

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.router import Router
from webob.multidict import MultiDict
from webtest.app import TestApp

import tempfile
import typing as t
import unittest


def app(spec: str) -> Router:
    """Prepare a Pyramid app."""

    def foo_view(request: Request) -> t.Dict[str, str]:
        """Return reversed string."""
        return {"bar": request.openapi_validated.body["bar"][::-1]}

    def multipart_view(request: Request) -> t.Dict[str, t.Union[str, t.List[str]]]:
        """Return reversed string."""
        body = request.openapi_validated.body
        return {
            "key1": body["key1"][::-1],
            "key2": [x[::-1] for x in body["key2"]],
            "key3": body["key3"].decode("utf-8")[::-1],
        }

    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.add_route("foo", "/foo")
        config.add_view(
            openapi=True,
            renderer="json",
            view=foo_view,
            route_name="foo",
        )
        config.add_route("multipart", "/multipart")
        config.add_view(
            openapi=True,
            renderer="json",
            view=multipart_view,
            route_name="multipart",
        )
        return config.make_wsgi_app()


OPENAPI_YAML = """
    openapi: "3.0.0"
    info:
      version: "1.0.0"
      title: Foo
    components:
      schemas:
        FooObject:
          type: object
          properties:
            bar:
              type: string
        BarObject:
          type: object
          properties:
            key1:
              type: string
            key2:
              type: array
              items:
                type: string
            key3:
              type: string
              format: binary
    paths:
      /foo:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/FooObject"
              application/x-www-form-urlencoded:
                schema:
                  $ref: "#/components/schemas/FooObject"
          responses:
            200:
              description: OK
      /multipart:
        post:
          requestBody:
            content:
              multipart/form-data:
                schema:
                  $ref: "#/components/schemas/BarObject"
          responses:
            200:
              description: OK
"""


class TestContentTypes(unittest.TestCase):
    """A suite of tests that make sure different body content types are supported."""

    def _testapp(self) -> TestApp:
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(OPENAPI_YAML.encode())
            document.seek(0)

            return TestApp(app(document.name))

    def test_post_json(self) -> None:
        """Post with `application/json`."""

        res = self._testapp().post_json("/foo", {"bar": "baz"}, status=200)
        self.assertEqual(res.json, {"bar": "zab"})

    def test_post_form(self) -> None:  # pragma: no cover
        """Post with `application/x-www-form-urlencoded`."""

        res = self._testapp().post("/foo", params={"bar": "baz"}, status=200)
        self.assertEqual(res.json, {"bar": "zab"})

    def test_post_multipart(self) -> None:
        """Post with `multipart/form-data`."""

        multi_dict = MultiDict()
        multi_dict.add("key1", "value1")
        multi_dict.add("key2", "value2.1")
        multi_dict.add("key2", "value2.2")
        multi_dict.add("key3", b"value3")

        res = self._testapp().post(
            "/multipart",
            multi_dict,
            content_type="multipart/form-data",
            status=200,
        )
        self.assertEqual(
            res.json,
            {
                "key1": "1eulav",
                "key2": ["1.2eulav", "2.2eulav"],
                "key3": "3eulav",
            },
        )


# This is almost the same as the previous test, but with OpenAPI 3.1.0.
# `multipart_view()` no longer needs to decode the bytes to a string.
def app310(spec: str) -> Router:
    """Prepare a Pyramid app."""

    def foo_view(request: Request) -> t.Dict[str, str]:
        """Return reversed string."""
        return {"bar": request.openapi_validated.body["bar"][::-1]}

    def multipart_view(request: Request) -> t.Dict[str, t.Union[str, t.List[str]]]:
        """Return reversed string."""
        body = request.openapi_validated.body
        return {
            "key1": body["key1"][::-1],
            "key2": [x[::-1] for x in body["key2"]],
            "key3": body["key3"][::-1],
        }

    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.add_route("foo", "/foo")
        config.add_view(
            openapi=True,
            renderer="json",
            view=foo_view,
            route_name="foo",
        )
        config.add_route("multipart", "/multipart")
        config.add_view(
            openapi=True,
            renderer="json",
            view=multipart_view,
            route_name="multipart",
        )
        return config.make_wsgi_app()


OPENAPI_YAML310 = """
    openapi: "3.1.0"
    info:
      version: "1.0.0"
      title: Foo
    components:
      schemas:
        FooObject:
          type: object
          properties:
            bar:
              type: string
        BarObject:
          type: object
          properties:
            key1:
              type: string
            key2:
              type: array
              items:
                type: string
            key3:
              type: string
              contentMediaType: application/octet-stream
    paths:
      /foo:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/FooObject"
              application/x-www-form-urlencoded:
                schema:
                  $ref: "#/components/schemas/FooObject"
          responses:
            200:
              description: OK
      /multipart:
        post:
          requestBody:
            content:
              multipart/form-data:
                schema:
                  $ref: "#/components/schemas/BarObject"
          responses:
            200:
              description: OK
"""


class TestContentTypes310(unittest.TestCase):
    """A suite of tests that make sure different body content types are supported."""

    def _testapp(self) -> TestApp:
        """Start up the app so that tests can send requests to it."""
        from webtest import TestApp

        with tempfile.NamedTemporaryFile() as document:
            document.write(OPENAPI_YAML310.encode())
            document.seek(0)

            return TestApp(app310(document.name))

    def test_post_json(self) -> None:
        """Post with `application/json`."""

        res = self._testapp().post_json("/foo", {"bar": "baz"}, status=200)
        self.assertEqual(res.json, {"bar": "zab"})

    def test_post_form(self) -> None:  # pragma: no cover
        """Post with `application/x-www-form-urlencoded`."""

        res = self._testapp().post("/foo", params={"bar": "baz"}, status=200)
        self.assertEqual(res.json, {"bar": "zab"})

    def test_post_multipart(self) -> None:
        """Post with `multipart/form-data`."""

        multi_dict = MultiDict()
        multi_dict.add("key1", "value1")
        multi_dict.add("key2", "value2.1")
        multi_dict.add("key2", "value2.2")
        multi_dict.add("key3", b"value3")

        res = self._testapp().post(
            "/multipart",
            multi_dict,
            content_type="multipart/form-data",
            status=200,
        )
        self.assertEqual(
            res.json,
            {
                "key1": "1eulav",
                "key2": ["1.2eulav", "2.2eulav"],
                "key3": "3eulav",
            },
        )
