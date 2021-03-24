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
openapi: "3.0.0"
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
            config.make_wsgi_app()


def test_register_routes_with_factory() -> None:
    """Test registration routes with root_factory."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(
                b"""\
openapi: "3.0.0"
info:
  version: "1.0.0"
  title: Foo API
paths:
  /foo:
    x-pyramid-route-name: foo
    x-pyramid-root-factory: pyramid_openapi3.tests.test_routes.dummy_factory
    get:
      responses:
        200:
          description: A foo
"""
            )
            tempdoc.seek(0)
            config.pyramid_openapi3_spec(tempdoc.name)
            config.pyramid_openapi3_register_routes()
            config.make_wsgi_app()
