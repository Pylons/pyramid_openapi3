"""Tests routes."""

from pyramid.httpexceptions import HTTPNotFound
from pyramid.request import Request
from pyramid.testing import testConfig
from webtest.app import TestApp

import pytest
import tempfile


def dummy_factory(request: Request) -> str:
    """Root factory for testing."""
    return "_DUMMY_"  # pragma: no cover


def test_register_routes_simple() -> None:
    """Test registration routes without root_factory."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(b"""\
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
""")
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
        ("pyramid_openapi3.spec_json", "/openapi.json"),
        ("foo", "/foo"),
        ("bar", "/bar"),
    ]


def test_register_routes_with_factory() -> None:
    """Test registration routes with root_factory."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(b"""\
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

""")
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
        ("pyramid_openapi3.spec_json", "/openapi.json", None),
        ("foo", "/foo", None),
        ("bar", "/bar", dummy_factory),
    ]


def test_register_routes_with_prefix() -> None:
    """Test registration routes with route_prefix."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(b"""\
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
""")
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
        ("pyramid_openapi3.spec_json", "/openapi.json"),
        ("foo", "/api/v1/foo"),
    ]


# GH #194 -- the `servers` URL is a mount point, not a route prefix.
GH194_SPEC = b"""\
openapi: "3.1.0"
info:
  version: "1.0.0"
  title: Foo API
servers:
  - url: /api
paths:
  /v2/users/:
    x-pyramid-route-name: users
    get:
      responses:
        "200":
          description: A list of users
          content:
            application/json:
              schema:
                type: array
                items:
                  type: string
"""


def _users_view(*args: object) -> list:
    """Return a response that validates against GH194_SPEC's 200."""
    return []


@pytest.mark.parametrize(
    ("route_prefix", "script_name", "path_info", "expected_status"),
    [
        # style A -- mounted at /api (SCRIPT_NAME), routes registered verbatim.
        # The `servers` prefix is the mount point, so verbatim is correct.
        pytest.param(None, "/api", "/v2/users/", 200, id="mounted-verbatim"),
        # style B -- app at the root, prefix baked into the routes explicitly.
        pytest.param("/api", "", "/api/v2/users/", 200, id="root-route_prefix"),
        # style C (the trap) -- mounting *and* route_prefix double-prefixes, so the
        # route expects /api/api/v2/users/ and the request 404s. This is why the
        # `servers` prefix must NOT be auto-derived: it would push every mounted app
        # (style A) into this broken state.
        pytest.param("/api", "/api", "/v2/users/", 404, id="mounted-and-route_prefix"),
    ],
)
def test_servers_url_is_mount_point_not_route_prefix(
    route_prefix: str | None, script_name: str, path_info: str, expected_status: int
) -> None:
    """GH #194: `servers` is a mount point, so verbatim registration is correct.

    Drive a real request through each supported deployment style (and the trap of
    combining them). The external URL is http://localhost/api/v2/users/ in every
    case; ``SCRIPT_NAME`` is the mount point, ``PATH_INFO`` is the remainder.
    """
    with testConfig() as config:
        config.include("pyramid_openapi3")
        # Render an unmatched route as a 404 response (like a real app) instead of
        # letting the raw HTTPNotFound propagate, so the style-C miss is observable.
        config.add_notfound_view(lambda request: HTTPNotFound())
        with tempfile.NamedTemporaryFile() as tempdoc:
            tempdoc.write(GH194_SPEC)
            tempdoc.seek(0)
            config.pyramid_openapi3_spec(tempdoc.name)
            # route_prefix=None is the directive's default (verbatim registration).
            config.pyramid_openapi3_register_routes(route_prefix=route_prefix)
            config.add_view(
                _users_view, route_name="users", renderer="json", openapi=True
            )
            test_app = TestApp(config.make_wsgi_app())
            response = test_app.get(
                path_info,
                extra_environ={"SCRIPT_NAME": script_name},
                expect_errors=True,
            )

    assert response.status_int == expected_status
