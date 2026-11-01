"""Test rendering with permissions."""

from pyramid import security
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.session import SignedCookieSessionFactory
from webtest.app import TestApp

import pytest
import typing as t

# The auth policies and pyramid.security.Allow/Authenticated are deprecated in
# Pyramid 2.0, but this file deliberately exercises them since they're still the
# canonical API on the oldest supported Pyramid (1.10.7).
pytestmark = [
    pytest.mark.filterwarnings(
        r"ignore:.*pyramid\.security\..*is deprecated in Pyramid 2\.0"
        ":DeprecationWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:Authentication and authorization policies have been deprecated"
        ":DeprecationWarning"
    ),
    # Pyramid 1.10.7 only, from the session code its auth policies use.
    pytest.mark.filterwarnings(
        "ignore:The default pickle serializer is deprecated:DeprecationWarning"
    ),
]


class DummyDefaultContext:  # noqa: D101
    @property
    def __acl__(self) -> list:
        """Read the deprecated names at request time, under pytestmark's filters."""
        return [(security.Allow, security.Authenticated, "view")]


def get_default_context(request: Request) -> DummyDefaultContext:
    """Return a dummy context."""
    return DummyDefaultContext()


@pytest.fixture
def simple_config() -> t.Generator[Configurator, None, None]:
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
    openapi: "3.1.0"
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
    ("route", "permission", "status"),
    [
        ("/api/v1/openapi.yaml", None, 403),
        ("/api/v1/openapi.yaml", NO_PERMISSION_REQUIRED, 200),
        ("/api/v1/", None, 403),
        ("/api/v1/", NO_PERMISSION_REQUIRED, 200),
    ],
)
def test_permission_for_specs(
    simple_config: Configurator,
    write_spec: t.Callable[..., str],
    route: str,
    permission: str,
    status: int,
) -> None:
    """Allow (200) or deny (403) access to the spec/explorer view."""
    spec_path = write_spec(OPENAPI_YAML.encode())

    simple_config.pyramid_openapi3_spec(
        spec_path,
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
    openapi: "3.1.0"
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
    ("route", "permission", "status"),
    [
        ("/api/v1/spec/openapi.yaml", "deny", 403),
        ("/api/v1/spec/openapi.yaml", NO_PERMISSION_REQUIRED, 200),
        ("/api/v1/spec/paths.yaml", "deny", 403),
        ("/api/v1/spec/paths.yaml", NO_PERMISSION_REQUIRED, 200),
        ("/api/v1/", "deny", 403),
        ("/api/v1/", NO_PERMISSION_REQUIRED, 200),
    ],
)
def test_permission_for_spec_directories(
    simple_config: Configurator,
    write_spec: t.Callable[..., str],
    route: str,
    permission: str,
    status: int,
) -> None:
    """Allow (200) or deny (403) access to the spec/explorer view."""
    write_spec(SPLIT_PATHS_YAML, "split/paths.yaml")
    spec_path = write_spec(SPLIT_OPENAPI_YAML, "split/openapi.yaml")

    simple_config.pyramid_openapi3_spec_directory(
        spec_path,
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
