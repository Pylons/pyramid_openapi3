"""Tests views."""

from collections.abc import Iterator
from contextlib import closing
from openapi_core.templating.paths.finders import APICallPathFinder
from openapi_core.validation.request.protocols import RequestValidator
from openapi_core.validation.response.protocols import ResponseValidator
from pathlib import Path
from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.interfaces import IRouteRequest
from pyramid.interfaces import IRoutesMapper
from pyramid.router import Router
from pyramid.testing import DummyRequest
from pyramid.testing import testConfig
from pyramid_openapi3.exceptions import RequestValidationError
from pyramid_openapi3.tests.utils import DummyStartResponse
from pyramid_openapi3.tests.utils import get_view
from pyramid_openapi3.tests.utils import make_request

import json
import pytest
import re
import typing as t

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


@pytest.fixture
def minimal_config(write_spec: t.Callable[..., str]) -> Iterator[Configurator]:
    """Yield a config with MINIMAL_DOCUMENT registered and served at /foo.yaml."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(
            write_spec(MINIMAL_DOCUMENT), route="/foo.yaml", route_name="foo_api_spec"
        )
        yield config


def test_add_spec_view(tmp_path: Path, minimal_config: Configurator) -> None:
    """Test registration of a view that serves the openapi document."""
    config = minimal_config
    # assert settings
    openapi_settings = config.registry.settings["pyramid_openapi3"]
    assert openapi_settings["filepath"] == str(tmp_path / "openapi.yaml")
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
    view = get_view(config, "foo_api_spec")
    assert view(request=None, context=None).body == MINIMAL_DOCUMENT


def test_add_spec_view_json(minimal_config: Configurator) -> None:
    """Test that the openapi document is also served as JSON, alongside YAML."""
    config = minimal_config
    # assert route
    mapper = config.registry.getUtility(IRoutesMapper)
    routes = mapper.get_routes()
    assert routes[1].name == "foo_api_spec_json"
    assert routes[1].path == "/foo.json"

    # assert view
    view = get_view(config, "foo_api_spec_json")
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
            match=re.escape(
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
        view = get_view(config, "__/foo/")
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
            match=re.escape(
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


def test_add_explorer_view(minimal_config: Configurator) -> None:
    """Test registration of a view serving the Swagger UI."""
    config = minimal_config
    config.pyramid_openapi3_add_explorer(ui_config={"deepLinking": False})
    view = get_view(config, "pyramid_openapi3.explorer")
    response = view(request=DummyRequest(config=config), context=None)
    assert b"<title>Swagger UI</title>" in response.body
    assert b"const oauthConfig = null;" in response.body
    assert b'"deepLinking": false' in response.body
    assert (
        b'"oauth2RedirectUrl": "http://example.com/docs/oauth2-redirect"'
        in response.body
    )


def test_add_explorer_oauth_view(minimal_config: Configurator) -> None:
    """Test registration of a view serving the Swagger UI with OAuth support."""
    config = minimal_config
    config.pyramid_openapi3_add_explorer(
        oauth_redirect_route="/dummy/oauth2-redirect",
        oauth_config={
            "usePkceWithAuthorizationCodeGrant": True,
        },
    )
    view = get_view(config, "pyramid_openapi3.explorer")
    response = view(request=DummyRequest(config=config), context=None)
    assert b"<title>Swagger UI</title>" in response.body
    assert b"ui.initOAuth(" in response.body
    assert b"usePkceWithAuthorizationCodeGrant" in response.body
    assert (
        b'"oauth2RedirectUrl": "http://example.com/dummy/oauth2-redirect"'
        in response.body
    )

    view = get_view(config, "pyramid_openapi3.explorer.oauth2-redirect")
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

        view = get_view(config, "foo_api_explorer")
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b'"url": "/foo/openapi.yaml"' in response.body

        view = get_view(config, "bar_api_explorer")
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

        view = get_view(config, "foo_api_explorer")
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b'"url": "/foo.yaml"' in response.body

        view = get_view(config, "bar_api_explorer")
        response = view(request=DummyRequest(config=config), context=None)
        assert b"<title>Swagger UI</title>" in response.body
        assert b'"url": "/bar.yaml"' in response.body


def test_explorer_view_missing_spec() -> None:
    """Test graceful failure if explorer view is not registered."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_explorer()

        view = get_view(config, "pyramid_openapi3.explorer")
        with pytest.raises(
            ConfigurationError,
            match=re.escape(
                "You need to call config.pyramid_openapi3_spec for the "
                "explorer to work."
            ),
        ):
            view(request=DummyRequest(config=config), context=None)


def test_openapi_view(minimal_config: Configurator) -> None:
    """Test registration a an openapi view."""
    config = minimal_config
    config.add_route("foo", "/foo")
    view_func = lambda *arg: "bar"  # noqa: E731
    config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")

    view = get_view(config, "foo")
    request = make_request(config, "foo", content_type="text/html")
    response = view(None, request)

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

        view = get_view(config, "foo")
        request = make_request(config, "foo", content_type="text/html")
        response = view(None, request)

        assert response.json == "foo"

        view = get_view(config, "bar")
        request = make_request(config, "bar", content_type="text/html")
        response = view(None, request)

        assert response.json == "bar"


PATH_ITEM_QUERY_DOCUMENT = b"""
    openapi: "3.1.0"
    info:
      version: "1.0.0"
      title: Foo API
    paths:
      /foo:
        parameters:
          - name: foo
            in: query
            required: true
            schema:
              type: integer
        get:
          responses:
            200:
              description: A foo
"""

OPERATION_PARAMETER_DOCUMENT = """
    openapi: "3.1.0"
    info:
      version: "1.0.0"
      title: Foo API
    paths:
      /foo:
        get:
          parameters:
            - name: foo
              in: {location}
              required: true
              schema:
                type: integer
          responses:
            200:
              description: A foo
"""


@pytest.mark.parametrize(
    ("document", "location", "value", "content_type"),
    [
        pytest.param(
            PATH_ITEM_QUERY_DOCUMENT,
            "query",
            {"params": {"foo": "1"}},
            "application/json",
            id="path_item_query",
        ),
        pytest.param(
            OPERATION_PARAMETER_DOCUMENT.format(location="header").encode(),
            "header",
            {"headers": {"foo": "1"}},
            "text/html",
            id="header",
        ),
        pytest.param(
            OPERATION_PARAMETER_DOCUMENT.format(location="cookie").encode(),
            "cookie",
            {"cookies": {"foo": "1"}},
            "text/html",
            id="cookie",
        ),
    ],
)
def test_required_parameter(
    write_spec: t.Callable[..., str],
    document: bytes,
    location: str,
    value: dict,
    content_type: str,
) -> None:
    """Test a required parameter is enforced, then accepted, where it's declared."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(
            write_spec(document), route="/foo.yaml", route_name="foo_api_spec"
        )
        config.add_route("foo", "/foo")
        view_func = lambda *arg: "foo"  # noqa: E731
        config.add_view(openapi=True, renderer="json", view=view_func, route_name="foo")
        view = get_view(config, "foo")

        request = make_request(config, "foo", content_type=content_type)
        with pytest.raises(
            RequestValidationError, match=f"Missing required {location} parameter: foo"
        ):
            view(None, request)

        request = make_request(config, "foo", content_type=content_type, **value)
        assert view(None, request).json == "foo"


@pytest.mark.parametrize(
    ("request_attrs", "present", "absent"),
    [
        pytest.param(
            {"csp_nonce": "test-nonce-123"},
            b'<script nonce="test-nonce-123">',
            b"<script>",
            id="with_csp_nonce",
        ),
        pytest.param({}, b"<script>", b"nonce=", id="without_csp_nonce"),
    ],
)
def test_add_explorer_view_csp_nonce(
    minimal_config: Configurator, request_attrs: dict, present: bytes, absent: bytes
) -> None:
    """Test explorer script tags carry the request's CSP nonce only when it has one."""
    config = minimal_config
    config.pyramid_openapi3_add_explorer()
    view = get_view(config, "pyramid_openapi3.explorer")

    response = view(request=DummyRequest(config=config, **request_attrs), context=None)

    assert present in response.body
    assert absent not in response.body
    assert b"<title>Swagger UI</title>" in response.body
