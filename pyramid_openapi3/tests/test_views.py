"""Tests views."""

from contextlib import closing
from dataclasses import dataclass
from openapi_core.templating.paths.finders import APICallPathFinder
from openapi_core.validation.request.protocols import RequestValidator
from openapi_core.validation.response.protocols import ResponseValidator
from pyramid.exceptions import ConfigurationError
from pyramid.interfaces import Interface
from pyramid.interfaces import IRouteRequest
from pyramid.interfaces import IRoutesMapper
from pyramid.interfaces import IView
from pyramid.interfaces import IViewClassifier
from pyramid.request import apply_request_extensions
from pyramid.router import Router
from pyramid.testing import DummyRequest
from pyramid.testing import testConfig
from pyramid_openapi3.exceptions import RequestValidationError

import json
import pytest
import typing as t


class DummyStartResponse:  # noqa: D101
    def __call__(self, status: str, headerlist: list[tuple[str, str]]) -> None:
        """WSGI start_response protocol."""
        self.status = status
        self.headerlist = headerlist


MINIMAL_DOCUMENT = b"""
    openapi: "3.1.0"
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

ALTERNATE_DOCUMENT = b"""
    openapi: "3.1.0"
    info:
      version: "1.0.0"
      title: Bar API
    paths:
      /bar:
        get:
          responses:
            200:
              description: A bar
"""

SPLIT_DOCUMENT = b"""
    openapi: "3.1.0"
    info:
      version: "1.0.0"
      title: Foo API
    paths:
      /foo:
        $ref: "paths.yaml#/foo"
"""

SPLIT_DOCUMENT_PATHS = b"""
    foo:
      get:
        responses:
          200:
            description: A foo
"""

ALTERNATE_SPLIT_DOCUMENT = b"""
    openapi: "3.1.0"
    info:
      version: "1.0.0"
      title: Bar API
    paths:
      /bar:
        $ref: "paths.yaml#/bar"
"""

ALTERNATE_SPLIT_DOCUMENT_PATHS = b"""
    bar:
      get:
        responses:
          200:
            description: A bar
"""


def test_add_spec_view(write_spec: t.Callable[..., str]) -> None:
    """Test registration of a view that serves the openapi document."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        # assert settings
        openapi_settings = config.registry.settings["pyramid_openapi3"]
        assert openapi_settings["filepath"] == spec_path
        assert openapi_settings["spec_route_name"] == "foo_api_spec"
        assert openapi_settings["spec"]["info"]["title"] == "Foo API"
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


def test_add_spec_view_json(write_spec: t.Callable[..., str]) -> None:
    """Test that the openapi document is also served as JSON, alongside YAML."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        # assert route
        mapper = config.registry.getUtility(IRoutesMapper)
        routes = mapper.get_routes()
        assert routes[1].name == "foo_api_spec_json"
        assert routes[1].path == "/foo.json"

        # assert view
        request = config.registry.queryUtility(IRouteRequest, name="foo_api_spec_json")
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=None, context=None)
        assert response.content_type == "application/json"
        spec = config.registry.settings["pyramid_openapi3"]["spec"]
        assert json.loads(response.body) == spec.read_value()


def test_add_spec_view_already_defined(write_spec: t.Callable[..., str]) -> None:
    """Test that creating a spec more than once raises an Exception."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        write_spec(SPLIT_DOCUMENT_PATHS, "split/paths.yaml")
        split_spec_path = write_spec(SPLIT_DOCUMENT, "split/openapi.yaml")

        config.pyramid_openapi3_spec_directory(
            split_spec_path, route="/foo", route_name="foo_api_spec"
        )

        spec_path = write_spec(MINIMAL_DOCUMENT)

        with pytest.raises(
            ConfigurationError,
            match=(
                "Spec has already been configured. You may only call "
                "pyramid_openapi3_spec or pyramid_openapi3_spec_directory once"
            ),
        ):
            config.pyramid_openapi3_spec(
                spec_path, route="/foo.yaml", route_name="foo_api_spec"
            )


def test_add_spec_view_directory(write_spec: t.Callable[..., str]) -> None:
    """Test registration of a view that serves the openapi document."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        write_spec(SPLIT_DOCUMENT_PATHS, "split/paths.yaml")
        split_spec_path = write_spec(SPLIT_DOCUMENT, "split/openapi.yaml")

        config.pyramid_openapi3_spec_directory(
            split_spec_path, route="/foo", route_name="foo_api_spec"
        )

        # assert settings
        openapi_settings = config.registry.settings["pyramid_openapi3"]
        assert openapi_settings["filepath"] == split_spec_path
        assert openapi_settings["spec_route_name"] == "foo_api_spec"
        assert openapi_settings["spec"]["info"]["title"] == "Foo API"

        # Make sure that the path (located in a different file) resolves correctly
        path = APICallPathFinder(spec=openapi_settings["spec"]).find(
            "get", "http://example.com/foo"
        )
        assert path is not None

        assert isinstance(openapi_settings["request_validator"], RequestValidator)
        assert isinstance(openapi_settings["response_validator"], ResponseValidator)

        # assert route
        # routes[0] is the static view, routes[1] is the route
        mapper = config.registry.getUtility(IRoutesMapper)
        routes = mapper.get_routes()
        assert routes[0].name == "__/foo/"
        assert routes[0].path == "/foo/*subpath"
        assert routes[1].name == "foo_api_spec"
        assert routes[1].path == "/foo/openapi.yaml"

        # assert view
        route_request = config.registry.queryUtility(IRouteRequest, name="foo_api_spec")
        static_request = config.registry.queryUtility(IRouteRequest, name="__/foo/")
        view = config.registry.adapters.registered(
            (IViewClassifier, static_request, Interface), IView, name=""
        )
        assert route_request is not None
        assert static_request is not None
        assert view is not None

        # assert router
        router = Router(config.registry)
        for path, document in [
            ("/foo/openapi.yaml", SPLIT_DOCUMENT),
            ("/foo/paths.yaml", SPLIT_DOCUMENT_PATHS),
        ]:
            with closing(router({"PATH_INFO": path}, DummyStartResponse())) as body:
                assert next(body) == document


def test_add_spec_view_directory_already_defined(
    write_spec: t.Callable[..., str],
) -> None:
    """Test that creating a spec more than once raises an Exception."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(spec_path, route="/foo", route_name="foo_api_spec")

        write_spec(SPLIT_DOCUMENT_PATHS, "split/paths.yaml")
        split_spec_path = write_spec(SPLIT_DOCUMENT, "split/openapi.yaml")

        with pytest.raises(
            ConfigurationError,
            match=(
                "Spec has already been configured. You may only call "
                "pyramid_openapi3_spec or pyramid_openapi3_spec_directory once"
            ),
        ):
            config.pyramid_openapi3_spec_directory(
                split_spec_path, route="/foo.yaml", route_name="foo_api_spec"
            )


def test_add_spec_view_directory_invalid_route(
    write_spec: t.Callable[..., str],
) -> None:
    """Test that creating a spec directory with a filename route raises an Exception."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        write_spec(SPLIT_DOCUMENT_PATHS, "split/paths.yaml")
        split_spec_path = write_spec(SPLIT_DOCUMENT, "split/openapi.yaml")

        with pytest.raises(
            ConfigurationError,
            match=(
                "Having route be a filename is not allowed when using a spec directory"
            ),
        ):
            config.pyramid_openapi3_spec_directory(
                split_spec_path, route="/foo.yaml", route_name="foo_api_spec"
            )


def test_add_explorer_view(write_spec: t.Callable[..., str]) -> None:
    """Test registration of a view serving the Swagger UI."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.pyramid_openapi3_add_explorer(ui_config={"deepLinking": False})
        request = config.registry.queryUtility(
            IRouteRequest, name="pyramid_openapi3.explorer"
        )
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b"const oauthConfig = null;" in response.body
        assert b'"deepLinking": false' in response.body
        assert (
            b'"oauth2RedirectUrl": "http://example.com/docs/oauth2-redirect"'
            in response.body
        )


def test_add_explorer_oauth_view(write_spec: t.Callable[..., str]) -> None:
    """Test registration of a view serving the Swagger UI with OAuth support."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.pyramid_openapi3_add_explorer(
            oauth_redirect_route="/dummy/oauth2-redirect",
            oauth_config={
                "usePkceWithAuthorizationCodeGrant": True,
            },
        )
        request = config.registry.queryUtility(
            IRouteRequest, name="pyramid_openapi3.explorer"
        )
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b"ui.initOAuth(" in response.body
        assert b"usePkceWithAuthorizationCodeGrant" in response.body
        assert (
            b'"oauth2RedirectUrl": "http://example.com/dummy/oauth2-redirect"'
            in response.body
        )

        request = config.registry.queryUtility(
            IRouteRequest, name="pyramid_openapi3.explorer.oauth2-redirect"
        )
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI: OAuth2 Redirect</title>" in response.body


def test_add_multiple_explorer_views_using_directory(
    write_spec: t.Callable[..., str],
) -> None:
    """Test registration of multiple views serving different Swagger UI."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        write_spec(SPLIT_DOCUMENT_PATHS, "foo/paths.yaml")
        foo_spec_path = write_spec(SPLIT_DOCUMENT, "foo/openapi.yaml")

        config.pyramid_openapi3_spec_directory(
            foo_spec_path, route="/foo", route_name="foo_api_spec", apiname="foo_api"
        )
        config.pyramid_openapi3_add_explorer(
            route="/foo_api/v1/", route_name="foo_api_explorer", apiname="foo_api"
        )

        write_spec(ALTERNATE_SPLIT_DOCUMENT_PATHS, "bar/paths.yaml")
        bar_spec_path = write_spec(ALTERNATE_SPLIT_DOCUMENT, "bar/openapi.yaml")

        config.pyramid_openapi3_spec_directory(
            bar_spec_path, route="/bar", route_name="bar_api_spec", apiname="bar_api"
        )
        config.pyramid_openapi3_add_explorer(
            route="/bar_api/v1/", route_name="bar_api_explorer", apiname="bar_api"
        )

        request = config.registry.queryUtility(IRouteRequest, name="foo_api_explorer")
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b'"url": "/foo/openapi.yaml"' in response.body

        request = config.registry.queryUtility(IRouteRequest, name="bar_api_explorer")
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b'"url": "/bar/openapi.yaml"' in response.body


def test_add_multiple_explorer_views(write_spec: t.Callable[..., str]) -> None:
    """Test registration of multiple views serving different Swagger UI."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path,
            route="/foo.yaml",
            route_name="foo_api_spec",
            apiname="foo_api",
        )
        config.pyramid_openapi3_add_explorer(
            route="/foo_api/v1/",
            route_name="foo_api_explorer",
            apiname="foo_api",
        )

        spec_path = write_spec(ALTERNATE_DOCUMENT, "alternate.yaml")

        config.pyramid_openapi3_spec(
            spec_path,
            route="/bar.yaml",
            route_name="bar_api_spec",
            apiname="bar_api",
        )
        config.pyramid_openapi3_add_explorer(
            route="/bar_api/v1/",
            route_name="bar_api_explorer",
            apiname="bar_api",
        )

        request = config.registry.queryUtility(IRouteRequest, name="foo_api_explorer")
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b'"url": "/foo.yaml"' in response.body

        request = config.registry.queryUtility(IRouteRequest, name="bar_api_explorer")
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b'"url": "/bar.yaml"' in response.body


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
            match=(
                "You need to call config.pyramid_openapi3_spec for the "
                "explorer to work."
            ),
        ):
            view(request=DummyRequest(config=config), context=None)


@dataclass
class DummyRoute:  # noqa: D101
    name: str
    pattern: str


def test_openapi_view(write_spec: t.Callable[..., str]) -> None:
    """Test registration a an openapi view."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "bar"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        request = DummyRequest(config=config, content_type="text/html")
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "bar"


def test_multiple_openapi_views(write_spec: t.Callable[..., str]) -> None:
    """Test registration multiple openapi views."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path,
            route="/foo.yaml",
            route_name="foo_api_spec",
            apiname="foo",
        )

        spec_path = write_spec(ALTERNATE_DOCUMENT, "alternate.yaml")

        config.pyramid_openapi3_spec(
            spec_path,
            route="/bar.yaml",
            route_name="bar_api_spec",
            apiname="bar",
        )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        config.add_route("bar", "/bar")
        view_func = lambda *arg: "bar"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="bar")

        # Simulate, that `check_all_routes` was called
        settings = config.registry.settings
        settings.setdefault("pyramid_openapi3", {})
        settings["pyramid_openapi3"].setdefault("routes", {})
        settings["pyramid_openapi3"]["routes"]["foo"] = "foo"
        settings["pyramid_openapi3"]["routes"]["bar"] = "bar"

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        request = DummyRequest(config=config, content_type="text/html")
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "foo"

        request_interface = config.registry.queryUtility(IRouteRequest, name="bar")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        request = DummyRequest(config=config, content_type="text/html")
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="bar", pattern="/bar")
        context = None
        response = view(context, request)

        assert response.json == "bar"


def test_path_item_parameters(write_spec: t.Callable[..., str]) -> None:
    """Test parameters declared on the path item are validated correctly."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        spec_path = write_spec(
            b'openapi: "3.1.0"\n'
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

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        # Test validation fails
        request = DummyRequest(config=config, content_type="application/json")
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        with pytest.raises(
            RequestValidationError, match="Missing required query parameter: foo"
        ):
            response = view(context, request)

        # Test validation succeeds
        request = DummyRequest(
            config=config, params={"foo": "1"}, content_type="application/json"
        )
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "foo"


def test_header_parameters(write_spec: t.Callable[..., str]) -> None:
    """Test parameters in header are validated correctly."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        spec_path = write_spec(
            b'openapi: "3.1.0"\n'
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

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        # Test validation fails
        request = DummyRequest(config=config, content_type="text/html")
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None

        with pytest.raises(
            RequestValidationError, match="Missing required header parameter: foo"
        ):
            response = view(context, request)

        # Test validation succeeds
        request = DummyRequest(
            config=config, headers={"foo": "1"}, content_type="text/html"
        )
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "foo"


def test_cookie_parameters(write_spec: t.Callable[..., str]) -> None:
    """Test parameters in cookie are validated correctly."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        spec_path = write_spec(
            b'openapi: "3.1.0"\n'
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

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

        request_interface = config.registry.queryUtility(IRouteRequest, name="foo")
        view = config.registry.adapters.registered(
            (IViewClassifier, request_interface, Interface), IView, name=""
        )
        # Test validation fails
        request = DummyRequest(config=config, content_type="text/html")
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        with pytest.raises(
            RequestValidationError, match="Missing required cookie parameter: foo"
        ):
            response = view(context, request)

        # Test validation succeeds
        request = DummyRequest(
            config=config, cookies={"foo": "1"}, content_type="text/html"
        )
        apply_request_extensions(request)
        request.matched_route = DummyRoute(name="foo", pattern="/foo")
        context = None
        response = view(context, request)

        assert response.json == "foo"


def test_add_explorer_view_with_csp_nonce(write_spec: t.Callable[..., str]) -> None:
    """Test explorer view includes CSP nonce when available on request."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.pyramid_openapi3_add_explorer()
        request = config.registry.queryUtility(
            IRouteRequest, name="pyramid_openapi3.explorer"
        )
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )

        # Test with CSP nonce
        dummy_request = DummyRequest(config=config)
        dummy_request.csp_nonce = "test-nonce-123"
        response = view(request=dummy_request, context=None)

        assert b'<script nonce="test-nonce-123">' in response.body
        assert b"<title>Swagger UI</title>" in response.body


def test_add_explorer_view_without_csp_nonce(write_spec: t.Callable[..., str]) -> None:
    """Test explorer view works normally when no CSP nonce is present."""
    with testConfig() as config:
        config.include("pyramid_openapi3")

        spec_path = write_spec(MINIMAL_DOCUMENT)

        config.pyramid_openapi3_spec(
            spec_path, route="/foo.yaml", route_name="foo_api_spec"
        )

        config.pyramid_openapi3_add_explorer()
        request = config.registry.queryUtility(
            IRouteRequest, name="pyramid_openapi3.explorer"
        )
        view = config.registry.adapters.registered(
            (IViewClassifier, request, Interface), IView, name=""
        )

        # Test without CSP nonce
        dummy_request = DummyRequest(config=config)
        response = view(request=dummy_request, context=None)

        assert b"<script>" in response.body
        assert b"nonce=" not in response.body
        assert b"<title>Swagger UI</title>" in response.body
