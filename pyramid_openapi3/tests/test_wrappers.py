"""Tests for the wrappers.py module."""

from dataclasses import dataclass
from pyramid.testing import DummyRequest
from pyramid_openapi3.wrappers import PyramidOpenAPIRequest
from pyramid_openapi3.wrappers import PyramidOpenAPIResponse


@dataclass
class DummyRoute:
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

    assert pyramid_request.host_url == "http://example.com"
    assert pyramid_request.path == "/foo"
    assert pyramid_request.method == "GET"

    openapi_request = PyramidOpenAPIRequest(pyramid_request)

    assert openapi_request.request == pyramid_request
    assert openapi_request.host_url == "http://example.com"
    assert openapi_request.path == "/foo"
    assert openapi_request.method == "get"
    assert openapi_request.path_pattern == "/foo"
    assert openapi_request.body == ""
    assert openapi_request.mimetype == "text/html"
    assert openapi_request.parameters == {
        "cookie": {"tasty-foo": "tasty-bar"},
        "header": {"X-Foo": "Bar"},
        "path": {"foo": "bar"},
        "query": {},
    }


def test_no_matched_route() -> None:
    """Test path_pattern when no route is matched."""
    pyramid_request = DummyRequest(path="/foo")
    pyramid_request.matched_route = None

    openapi_request = PyramidOpenAPIRequest(pyramid_request)
    assert openapi_request.path_pattern == "/foo"


def test_mapped_values_response() -> None:
    """Test that values are correctly mapped from pyramid's Response."""
    pyramid_request = DummyRequest()

    assert pyramid_request.response.body == b""
    assert pyramid_request.response.status_code == 200
    assert pyramid_request.response.content_type == "text/html"

    openapi_response = PyramidOpenAPIResponse(pyramid_request.response)

    assert openapi_response.response == pyramid_request.response
    assert openapi_response.data == b""
    assert openapi_response.status_code == 200
    assert openapi_response.mimetype == "text/html"
