"""Tests for the wrappers.py module."""

from dataclasses import dataclass
from openapi_core.validation.request.datatypes import RequestParameters
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

    openapi_request = PyramidOpenAPIRequest.create(pyramid_request)

    assert openapi_request.full_url_pattern == "http://example.com/foo"
    assert openapi_request.method == "get"
    assert openapi_request.body == ""
    assert openapi_request.mimetype == "text/html"
    assert openapi_request.parameters == RequestParameters(
        path={"foo": "bar"},
        query={},
        header={"X-Foo": "Bar"},
        cookie={"tasty-foo": "tasty-bar"},
    )


def test_no_matched_route() -> None:
    """Test path_pattern when no route is matched."""
    pyramid_request = DummyRequest(path="/foo")
    pyramid_request.matched_route = None
    pyramid_request.content_type = "text/html"

    openapi_request = PyramidOpenAPIRequest.create(pyramid_request)
    assert openapi_request.full_url_pattern == "http://example.com/foo"


def test_mapped_values_response() -> None:
    """Test that values are correctly mapped from pyramid's Response."""
    pyramid_request = DummyRequest()

    assert pyramid_request.response.body == b""
    assert pyramid_request.response.status_code == 200
    assert pyramid_request.response.content_type == "text/html"

    openapi_response = PyramidOpenAPIResponse.create(pyramid_request.response)

    assert openapi_response.data == b""
    assert openapi_response.status_code == 200
    assert openapi_response.mimetype == "text/html"
