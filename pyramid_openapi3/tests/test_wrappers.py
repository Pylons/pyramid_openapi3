"""Tests for the wrappers.py module."""

from dataclasses import dataclass
from openapi_core.validation.request.datatypes import RequestParameters
from pyramid.request import Request
from pyramid.testing import DummyRequest
from pyramid_openapi3.wrappers import PyramidOpenAPIRequest
from pyramid_openapi3.wrappers import PyramidOpenAPIResponse


@dataclass
class DummyRoute:  # noqa: D101
    name: str
    pattern: str


def test_mapped_values_request() -> None:
    """Test that values are correctly mapped from pyramid's Request."""

    pyramid_request = DummyRequest(path="/foo")
    pyramid_request.matched_route = DummyRoute(name="foo", pattern="/foo")
    pyramid_request.matchdict["foo"] = "bar"
    pyramid_request.headers["X-Foo"] = "Bar"
    pyramid_request.cookies["tasty-foo"] = "tasty-bar"
    pyramid_request.content_type = "text/html"

    assert pyramid_request.application_url == "http://example.com"
    assert pyramid_request.path_info == "/foo"
    assert pyramid_request.method == "GET"

    openapi_request = PyramidOpenAPIRequest(pyramid_request)

    assert openapi_request.parameters == RequestParameters(
        path={"foo": "bar"},
        query={},
        header={"X-Foo": "Bar"},
        cookie={"tasty-foo": "tasty-bar"},
    )
    assert openapi_request.host_url == "http://example.com"
    assert openapi_request.path == "/foo"
    assert openapi_request.path_pattern == "/foo"
    assert openapi_request.method == "get"
    assert openapi_request.body == ""
    assert openapi_request.mimetype == "text/html"
    assert openapi_request.content_type == "text/html"


def test_relative_app_request() -> None:
    """Test that values are correctly mapped from pyramid's Request."""

    pyramid_request = Request.blank("/foo", base_url="http://example.com/subpath")
    pyramid_request.matched_route = DummyRoute(name="foo", pattern="/foo")
    pyramid_request.matchdict = {"foo": "bar"}
    pyramid_request.headers["X-Foo"] = "Bar"
    pyramid_request.cookies["tasty-foo"] = "tasty-bar"
    pyramid_request.content_type = "text/html"

    assert pyramid_request.host_url == "http://example.com"
    assert pyramid_request.path_info == "/foo"
    assert pyramid_request.method == "GET"

    openapi_request = PyramidOpenAPIRequest(pyramid_request)

    assert openapi_request.parameters == RequestParameters(
        path={"foo": "bar"},
        query={},
        header=pyramid_request.headers,
        cookie={"tasty-foo": "tasty-bar"},
    )
    assert openapi_request.host_url == "http://example.com"
    assert openapi_request.path == "/subpath/foo"
    assert openapi_request.path_pattern == "/foo"
    assert openapi_request.method == "get"
    assert openapi_request.body == b""
    assert openapi_request.mimetype == "text/html"
    assert openapi_request.content_type == "text/html"


def test_no_matched_route() -> None:
    """Test path_pattern when no route is matched."""
    pyramid_request = DummyRequest(path="/foo")
    pyramid_request.matched_route = None
    pyramid_request.content_type = "text/html"

    openapi_request = PyramidOpenAPIRequest(pyramid_request)
    assert openapi_request.host_url == "http://example.com"
    assert openapi_request.path == "/foo"
    assert openapi_request.path_pattern == "/foo"


def test_mapped_values_response() -> None:
    """Test that values are correctly mapped from pyramid's Response."""
    pyramid_request = DummyRequest()

    assert pyramid_request.response.body == b""
    assert pyramid_request.response.status_code == 200
    assert pyramid_request.response.content_type == "text/html"

    openapi_response = PyramidOpenAPIResponse(pyramid_request.response)

    assert openapi_response.data == b""
    assert openapi_response.status_code == 200
    assert openapi_response.mimetype == "text/html"
    assert openapi_response.content_type == "text/html"
    assert openapi_response.headers == pyramid_request.response.headers
