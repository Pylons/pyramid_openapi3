"""Test rendering with permissions."""

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.session import SignedCookieSessionFactory
from webtest.app import TestApp

import os
import pytest
import tempfile

DEFAULT_ACL = [
    (Allow, Authenticated, "view"),
]


class DummyDefaultContext(object):

    __acl__ = DEFAULT_ACL


def get_default_context(request) -> DummyDefaultContext:
    """Return a dummy context."""
    return DummyDefaultContext()


@pytest.fixture
def simple_config() -> Configurator:
    """Prepare the base configuration needed for the Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")

        # Setup security
        config.set_default_permission("view")
        config.set_session_factory(SignedCookieSessionFactory("itsaseekreet"))
        config.set_authentication_policy(SessionAuthenticationPolicy())
        config.set_authorization_policy(ACLAuthorizationPolicy())
        config.set_root_factory(get_default_context)

        yield config


OPENAPI_YAML = """
    openapi: "3.0.0"
    info:
      version: "1.0.0"
      title: Foo
    paths:
      /foo:
        post:
          parameters:
            - name: bar
              in: query
              schema:
                type: integer
          responses:
            200:
              description: Say hello
"""


@pytest.mark.parametrize(
    "route,permission,status",
    (
        ("/api/v1/openapi.yaml", None, 403),
        ("/api/v1/openapi.yaml", NO_PERMISSION_REQUIRED, 200),
        ("/api/v1/", None, 403),
        ("/api/v1/", NO_PERMISSION_REQUIRED, 200),
    ),
)
def test_permission_for_specs(simple_config, route, permission, status) -> None:
    """Allow (200) or deny (403) access to the spec/explorer view."""
    with tempfile.NamedTemporaryFile() as document:
        document.write(OPENAPI_YAML.encode())
        document.seek(0)

        simple_config.pyramid_openapi3_spec(
            document.name,
            route="/api/v1/openapi.yaml",
            route_name="api_spec",
            permission=permission,
        )
        simple_config.pyramid_openapi3_add_explorer(
            route="/api/v1/",
            route_name="api_explorer",
            permission=permission,
        )
        simple_config.add_route("foo", "/foo")

        testapp = TestApp(simple_config.make_wsgi_app())

        testapp.get(route, status=status)


SPLIT_OPENAPI_YAML = b"""
    openapi: "3.0.0"
    info:
      version: "1.0.0"
      title: Foo API
    paths:
      /foo:
        $ref: "paths.yaml#/foo"
"""

SPLIT_PATHS_YAML = b"""
    foo:
      post:
        parameters:
          - name: bar
            in: query
            schema:
              type: integer
        responses:
          200:
            description: Say hello
"""


@pytest.mark.parametrize(
    "route,permission,status",
    (
        ("/api/v1/spec/openapi.yaml", "deny", 403),
        ("/api/v1/spec/openapi.yaml", NO_PERMISSION_REQUIRED, 200),
        ("/api/v1/spec/paths.yaml", "deny", 403),
        ("/api/v1/spec/paths.yaml", NO_PERMISSION_REQUIRED, 200),
        ("/api/v1/", "deny", 403),
        ("/api/v1/", NO_PERMISSION_REQUIRED, 200),
    ),
)
def test_permission_for_spec_directories(
    simple_config, route, permission, status
) -> None:
    """Allow (200) or deny (403) access to the spec/explorer view."""
    with tempfile.TemporaryDirectory() as directory:
        spec_name = os.path.join(directory, "openapi.yaml")
        spec_paths_name = os.path.join(directory, "paths.yaml")
        with open(spec_name, "wb") as f:
            f.write(SPLIT_OPENAPI_YAML)
        with open(spec_paths_name, "wb") as f:
            f.write(SPLIT_PATHS_YAML)

        simple_config.pyramid_openapi3_spec_directory(
            spec_name,
            route="/api/v1/spec",
            route_name="api_spec",
            permission=permission,
        )
        simple_config.pyramid_openapi3_add_explorer(
            route="/api/v1/",
            route_name="api_explorer",
            permission=permission,
        )
        simple_config.add_route("foo", "/foo")

        testapp = TestApp(simple_config.make_wsgi_app())

        testapp.get(route, status=status)
