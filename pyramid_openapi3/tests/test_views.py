"""Tests views."""

from dataclasses import dataclass
from openapi_core.shortcuts import RequestValidator
from openapi_core.shortcuts import ResponseValidator
from pyramid.exceptions import ConfigurationError
from pyramid.interfaces import IRouteRequest
from pyramid.interfaces import IRoutesMapper
from pyramid.interfaces import IView
from pyramid.interfaces import IViewClassifier
from pyramid.testing import DummyRequest
from pyramid.testing import testConfig
from pyramid_openapi3.exceptions import RequestValidationError
from zope.interface import Interface

import pytest
import tempfile

MINIMAL_DOCUMENT = b"""
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
"""


def test_add_spec_view() -> None:
    """Test registration of a view that serves the openapi document."""

    with testConfig() as config:
        config.include("pyramid_openapi3")

        with tempfile.NamedTemporaryFile() as document:
            document.write(MINIMAL_DOCUMENT)
            document.seek(0)

            config.pyramid_openapi3_spec(
                document.name, route="/foo.yaml", route_name="foo_api_spec"
            )

            # assert settings
            openapi_settings = config.registry.settings["pyramid_openapi3"]
            assert openapi_settings["filepath"] == document.name
            assert openapi_settings["spec_route_name"] == "foo_api_spec"
            assert openapi_settings["spec"].info.title == "Foo API"
            assert isinstance(openapi_settings["request_validator"], RequestValidator)
            assert isinstance(openapi_settings["response_validator"], ResponseValidator)

            # assert route
            mapper = config.registry.getUtility(IRoutesMapper)
            routes = mapper.get_routes()
            assert routes[0].name == "foo_api_spec"
            assert routes[0].path == "/foo.yaml"

            # assert view
            request = config.registry.queryUtility(IRouteRequest, name="foo_api_spec")
            view = config.registry.adapters.registered(
                (IViewClassifier, request, Interface), IView, name=""
            )
            assert view(request=None, context=None).body == MINIMAL_DOCUMENT


def test_add_explorer_view() -> None:
    """Test registration of a view serving the Swagger UI."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        with tempfile.NamedTemporaryFile() as document:
            document.write(MINIMAL_DOCUMENT)
            document.seek(0)

            config.pyramid_openapi3_spec(
                document.name, route="/foo.yaml", route_name="foo_api_spec"
            )

        config.pyramid_openapi3_add_explorer()
        request = config.registry.queryUtility(
            IRouteRequest, name="pyramid_openapi3.explorer"
        )
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body


def test_explorer_view_missing_spec() -> None:
    """Test graceful failure if explorer view is not registered."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_explorer()

        request = config.registry.queryUtility(
            IRouteRequest, name="pyramid_openapi3.explorer"
        )
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        with pytest.raises(
            ConfigurationError,
            match="You need to call config.pyramid_openapi3_spec for explorer to work.",
        ):
            view(request=DummyRequest(config=config), context=None)


@dataclass
class DummyRoute:
    name: str
    pattern: str


def test_openapi_view() -> None:
    """Test registration a an openapi view."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        with tempfile.NamedTemporaryFile() as document:
            document.write(MINIMAL_DOCUMENT)
            document.seek(0)

            config.pyramid_openapi3_spec(
                document.name, route="/foo.yaml", route_name="foo_api_spec"
            )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "bar"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        request = DummyRequest(config=config, content_type="text/html")
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "bar"


def test_path_parameters() -> None:
    """Test parameters in path are validated correctly."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as document:
            document.write(
                b'openapi: "3.0.0"\n'
                b"info:\n"
                b'  version: "1.0.0"\n'
                b"  title: Foo API\n"
                b"paths:\n"
                b"  /foo:\n"
                b"    parameters:\n"
                b"      - name: foo\n"
                b"        in: query\n"
                b"        required: true\n"
                b"        schema:\n"
                b"          type: integer\n"
                b"    get:\n"
                b"      responses:\n"
                b"        200:\n"
                b"          description: A foo\n"
            )
            document.seek(0)

            config.pyramid_openapi3_spec(
                document.name, route="/foo.yaml", route_name="foo_api_spec"
            )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731  # pragma: no branch
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        # Test validation fails
        request = DummyRequest(config=config, content_type="application/json")
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        with pytest.raises(
            RequestValidationError, match="Missing required parameter: foo"
        ):
            response = view(context, request)

        # Test validation succeeds
        request = DummyRequest(
            config=config, params={"foo": "1"}, content_type="application/json"
        )
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "foo"


def test_header_parameters() -> None:
    """Test parameters in header are validated correctly."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as document:
            document.write(
                b'openapi: "3.0.0"\n'
                b"info:\n"
                b'  version: "1.0.0"\n'
                b"  title: Foo API\n"
                b"paths:\n"
                b"  /foo:\n"
                b"    get:\n"
                b"      parameters:\n"
                b"        - name: foo\n"
                b"          in: header\n"
                b"          required: true\n"
                b"          schema:\n"
                b"            type: integer\n"
                b"      responses:\n"
                b"        200:\n"
                b"          description: A foo\n"
            )
            document.seek(0)

            config.pyramid_openapi3_spec(
                document.name, route="/foo.yaml", route_name="foo_api_spec"
            )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731  # pragma: no branch
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        # Test validation fails
        request = DummyRequest(config=config, content_type="text/html")
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None

        with pytest.raises(
            RequestValidationError, match="Missing required parameter: foo"
        ):
            response = view(context, request)

        # Test validation succeeds
        request = DummyRequest(
            config=config, headers={"foo": "1"}, content_type="text/html"
        )
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "foo"


def test_cookie_parameters() -> None:
    """Test parameters in cookie are validated correctly."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        with tempfile.NamedTemporaryFile() as document:
            document.write(
                b'openapi: "3.0.0"\n'
                b"info:\n"
                b'  version: "1.0.0"\n'
                b"  title: Foo API\n"
                b"paths:\n"
                b"  /foo:\n"
                b"    get:\n"
                b"      parameters:\n"
                b"        - name: foo\n"
                b"          in: cookie\n"
                b"          required: true\n"
                b"          schema:\n"
                b"            type: integer\n"
                b"      responses:\n"
                b"        200:\n"
                b"          description: A foo\n"
            )
            document.seek(0)

            config.pyramid_openapi3_spec(
                document.name, route="/foo.yaml", route_name="foo_api_spec"
            )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731  # pragma: no branch
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        # Test validation fails
        request = DummyRequest(config=config, content_type="text/html")
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        with pytest.raises(
            RequestValidationError, match="Missing required parameter: foo"
        ):
            response = view(context, request)

        # Test validation succeeds
        request = DummyRequest(
            config=config, cookies={"foo": "1"}, content_type="text/html"
        )
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "foo"
