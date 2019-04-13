"""Tests views."""

from openapi_core.shortcuts import RequestValidator
from openapi_core.shortcuts import ResponseValidator
from pyramid.interfaces import IRouteRequest
from pyramid.interfaces import IRoutesMapper
from pyramid.interfaces import IView
from pyramid.interfaces import IViewClassifier
from pyramid.testing import testConfig
from zope.interface import Interface

import tempfile


def test_add_spec_view():
    """Test registration of a view that serves the openapi document."""

    with testConfig() as config:
        config.include("pyramid_openapi3")

        with tempfile.NamedTemporaryFile() as document:
            # fmt: off
            document.write(
                b'openapi: "3.0.0"\n'
                b'info:\n'
                b'  version: "1.0.0"\n'
                b'  title: Foo API\n'
                b'paths:\n'
                b'  /pets:\n'
                b'    get:\n'
                b'      responses:\n'
                b'        200:\n'
                b'          description: An paged array of pets\n'
            )
            # fmt: on
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
            assert view(request=None, context=None).body == (
                b'openapi: "3.0.0"\n'
                b"info:\n"
                b'  version: "1.0.0"\n'
                b"  title: Foo API\n"
                b"paths:\n"
                b"  /pets:\n"
                b"    get:\n"
                b"      responses:\n"
                b"        200:\n"
                b"          description: An paged array of pets\n"
            )


def test_add_validation_error_view():
    """Test registration of a view for rendering validation errors."""
    with testConfig() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_validation_error_view("foo_view")
        assert (
            config.registry._pyramid_openapi3_validation_view_name  # noqa: SF01
            == "foo_view"
        )
