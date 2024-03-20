"""Tests routes."""

from pyramid.request import Request
from pyramid.testing import testConfig

import tempfile


def dummy_factory(request: Request) -> str:
    """Root factory for testing."""
    return "_DUMMY_"  # pragma: no cover


def test_register_routes_simple() -> None:
    """Test registration routes without root_factory."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(
                b"""\
openapi: "3.1.0"
info:
  version: "1.0.0"
  title: Foo API
paths:
  /foo:
    x-pyramid-route-name: foo
    get:
      responses:
        200:
          description: A foo
  /bar:
    get:
      responses:
        200:
          description: A bar
"""
            )
            tempdoc.seek(0)
            config.pyramid_openapi3_spec(tempdoc.name)
            config.pyramid_openapi3_register_routes()
            config.add_route("bar", "/bar")
            app = config.make_wsgi_app()

    routes = [
        (i["introspectable"]["name"], i["introspectable"]["pattern"])
        for i in app.registry.introspector.get_category("routes")
    ]
    assert routes == [
        ("pyramid_openapi3.spec", "/openapi.yaml"),
        ("foo", "/foo"),
        ("bar", "/bar"),
    ]


def test_register_routes_with_factory() -> None:
    """Test registration routes with root_factory."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(
                b"""\
openapi: "3.1.0"
info:
  version: "1.0.0"
  title: Foo API
paths:
  /foo:
    x-pyramid-route-name: foo
    get:
      responses:
        200:
          description: A foo
  /bar:
    x-pyramid-route-name: bar
    x-pyramid-root-factory: pyramid_openapi3.tests.test_routes.dummy_factory
    get:
      responses:
        200:
          description: A bar

"""
            )
            tempdoc.seek(0)
            config.pyramid_openapi3_spec(tempdoc.name)
            config.pyramid_openapi3_register_routes()
            app = config.make_wsgi_app()

    routes = [
        (
            i["introspectable"]["name"],
            i["introspectable"]["pattern"],
            i["introspectable"]["factory"],
        )
        for i in app.registry.introspector.get_category("routes")
    ]
    assert routes == [
        ("pyramid_openapi3.spec", "/openapi.yaml", None),
        ("foo", "/foo", None),
        ("bar", "/bar", dummy_factory),
    ]


def test_register_routes_with_prefix() -> None:
    """Test registration routes with route_prefix."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(
                b"""\
openapi: "3.1.0"
info:
  version: "1.0.0"
  title: Foo API
servers:
  - url: /api/v1
paths:
  /foo:
    x-pyramid-route-name: foo
    get:
      responses:
        200:
          description: A foo
"""
            )
            tempdoc.seek(0)
            config.pyramid_openapi3_spec(tempdoc.name)
            config.pyramid_openapi3_register_routes(route_prefix="/api/v1")
            app = config.make_wsgi_app()

    routes = [
        (i["introspectable"]["name"], i["introspectable"]["pattern"])
        for i in app.registry.introspector.get_category("routes")
    ]
    assert routes == [
        ("pyramid_openapi3.spec", "/openapi.yaml"),
        ("foo", "/api/v1/foo"),
    ]
