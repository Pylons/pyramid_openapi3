"""Tests for app creation when using pyramid_openapi3."""
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.testing import testConfig
from pyramid_openapi3 import MissingEndpointsError

import logging
import pytest
import tempfile
import typing as t

DOCUMENT = b"""
    openapi: "3.0.0"
    info:
      version: "1.0.0"
      title: Foo API
    paths:
      /foo:
        get:
          responses:
            200:
              description: A foo
        post:
          responses:
            200:
              description: A POST foo
      /bar:
        get:
          responses:
            200:
              description: A bar
"""


def foo_view(request: Request) -> str:
    """Return a dummy string."""
    return "Foo"  # pragma: no cover


def bar_view(request: Request) -> str:
    """Return a dummy string."""
    return "Bar"  # pragma: no cover


@pytest.fixture
def document() -> t.Generator[t.IO, None, None]:
    """Load the DOCUMENT into a temp file."""
    with tempfile.NamedTemporaryFile() as document:
        document.write(DOCUMENT)
        document.seek(0)

        yield document


@pytest.fixture
def simple_config() -> Configurator:
    """Config fixture."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        yield config


@pytest.fixture
def app_config(
    simple_config: Configurator, document: t.IO
) -> t.Generator[Configurator, None, None]:
    """Incremented fixture that loads the DOCUMENT above into the config."""
    simple_config.pyramid_openapi3_spec(
        document.name, route="/foo.yaml", route_name="foo_api_spec"
    )
    yield simple_config


def test_all_routes(app_config: Configurator) -> None:
    """Test case showing that an app can be created with all routes define."""
    app_config.add_route(name="foo", pattern="/foo")
    app_config.add_route(name="bar", pattern="/bar")
    app_config.add_view(
        foo_view, route_name="foo", renderer="string", request_method="OPTIONS"
    )
    app_config.add_view(
        bar_view, route_name="bar", renderer="string", request_method="GET"
    )

    app_config.make_wsgi_app()


def test_missing_routes(app_config: Configurator) -> None:
    """Test case showing app creation fails, when define routes are missing."""
    app_config.add_route(name="foo", pattern="/foo")
    app_config.add_view(
        foo_view, route_name="foo", renderer="string", request_method="GET"
    )

    with pytest.raises(MissingEndpointsError) as ex:
        app_config.make_wsgi_app()

    assert "/bar" in ex.value.missing


def test_disable_endpoint_validation(app_config: Configurator, caplog) -> None:
    """Test case showing app creation whilst disabling endpoint validation."""
    caplog.set_level(logging.DEBUG)
    app_config.registry.settings.get("pyramid_openapi3").setdefault(
        "enable_endpoint_validation", False
    )
    app_config.add_route(name="foo", pattern="/foo")
    app_config.add_view(
        foo_view, route_name="foo", renderer="string", request_method="GET"
    )

    app_config.make_wsgi_app()

    assert "Endpoint validation against specification is disabled" in caplog.text


def test_unconfigured_app(simple_config: Configurator) -> None:
    """Asserts the app can be created if no spec has been defined."""
    simple_config.add_route(name="foo", pattern="/foo")
    simple_config.add_view(
        foo_view, route_name="foo", renderer="string", request_method="OPTIONS"
    )

    with pytest.warns(UserWarning, match="pyramid_openapi3 settings not found"):
        simple_config.make_wsgi_app()
