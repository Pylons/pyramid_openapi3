"""Test different request body content types."""

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.router import Router
from webob.multidict import MultiDict
from webtest.app import TestApp

import pytest
import typing as t


def app(spec: str, read_binary: t.Callable[[t.Any], str]) -> Router:
    """Prepare a Pyramid app.

    `read_binary` turns the validated binary field `key3` into a str.
    """

    def foo_view(request: Request) -> dict[str, str]:
        """Return reversed string."""
        return {"bar": request.openapi_validated.body["bar"][::-1]}

    def multipart_view(request: Request) -> dict[str, str | list[str]]:
        """Return reversed string."""
        body = request.openapi_validated.body
        return {
            "key1": body["key1"][::-1],
            "key2": [x[::-1] for x in body["key2"]],
            "key3": read_binary(body["key3"])[::-1],
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


# OpenAPI 3.0's `format: binary` unmarshals to bytes and 3.1's
# `contentMediaType` leaves a str, so each version gets the matching reader.
@pytest.fixture(
    params=[(OPENAPI_YAML, bytes.decode), (OPENAPI_YAML310, str)], ids=["3.0", "3.1"]
)
def testapp(
    request: pytest.FixtureRequest, write_spec: t.Callable[..., str]
) -> TestApp:
    """Start up the app for one OpenAPI version so tests can send requests to it."""
    spec, read_binary = request.param
    return TestApp(app(write_spec(spec.encode()), read_binary))


class TestContentTypes:
    """A suite of tests that make sure different body content types are supported."""

    def test_post_json(self, testapp: TestApp) -> None:
        """Post with `application/json`."""
        res = testapp.post_json("/foo", {"bar": "baz"}, status=200)
        assert res.json == {"bar": "zab"}

    def test_post_form(self, testapp: TestApp) -> None:
        """Post with `application/x-www-form-urlencoded`."""
        res = testapp.post("/foo", params={"bar": "baz"}, status=200)
        assert res.json == {"bar": "zab"}

    def test_post_multipart(self, testapp: TestApp) -> None:
        """Post with `multipart/form-data`."""
        multi_dict = MultiDict()
        multi_dict.add("key1", "value1")
        multi_dict.add("key2", "value2.1")
        multi_dict.add("key2", "value2.2")
        multi_dict.add("key3", b"value3")

        res = testapp.post(
            "/multipart",
            multi_dict,
            content_type="multipart/form-data",
            status=200,
        )
        assert res.json == {
            "key1": "1eulav",
            "key2": ["1.2eulav", "2.2eulav"],
            "key3": "3eulav",
        }
