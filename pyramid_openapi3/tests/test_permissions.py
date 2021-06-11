"""Test rendering with permissions."""

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.router import Router
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.session import SignedCookieSessionFactory
from webtest.app import TestApp

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


def app(spec: str, permission: str) -> Router:
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")

        # Setup security
        config.set_default_permission("view")
        config.set_session_factory(SignedCookieSessionFactory("itsaseekreet"))
        config.set_authentication_policy(SessionAuthenticationPolicy())
        config.set_authorization_policy(ACLAuthorizationPolicy())
        config.set_root_factory(get_default_context)

        config.pyramid_openapi3_spec(
            spec,
            route="/api/v1/openapi.yaml",
            route_name="api_spec",
            permission=permission,
        )
        config.pyramid_openapi3_add_explorer(
            route="/api/v1/",
            route_name="api_explorer",
            permission=permission,
        )
        config.add_route("foo", "/foo")
        return config.make_wsgi_app()


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
def test_permission_for_specs(route, permission, status) -> None:
    """Allow (200) or deny (403) access to the spec/explorer view."""
    with tempfile.NamedTemporaryFile() as document:
        document.write(OPENAPI_YAML.encode())
        document.seek(0)

        testapp = TestApp(app(document.name, permission))

        testapp.get(route, status=status)
