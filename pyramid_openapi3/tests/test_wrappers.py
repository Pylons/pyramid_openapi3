"""Tests for the wrappers.py module."""

from dataclasses import dataclass
from openapi_core.validation.request.datatypes import RequestParameters
from pyramid.request import Request
from pyramid.testing import DummyRequest
from pyramid_openapi3.wrappers import PyramidOpenAPIRequestFactory
from pyramid_openapi3.wrappers import PyramidOpenAPIResponseFactory
from webob.multidict import MultiDict


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

    assert pyramid_request.application_url == "http://example.com"
    assert pyramid_request.path_info == "/foo"
    assert pyramid_request.method == "GET"

    openapi_request = PyramidOpenAPIRequestFactory.create(pyramid_request)

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

    openapi_request = PyramidOpenAPIRequestFactory.create(pyramid_request)

    assert openapi_request.full_url_pattern == "http://example.com/subpath/foo"
    assert openapi_request.method == "get"
    assert openapi_request.body == b""
    assert openapi_request.mimetype == "text/html"
    assert openapi_request.parameters == RequestParameters(
        path={"foo": "bar"},
        query={},
        header=pyramid_request.headers.items(),
        cookie={"tasty-foo": "tasty-bar"},
    )


def test_form_data_request() -> None:
    """Test that request.POST is used as the body in case of form-data."""
    multi_dict = MultiDict()
    multi_dict.add("key1", "value1")
    multi_dict.add("key2", "value2.1")
    multi_dict.add("key2", "value2.2")
    pyramid_request = DummyRequest(path="/foo", post=multi_dict)
    pyramid_request.matched_route = DummyRoute(name="foo", pattern="/foo")
    pyramid_request.content_type = "multipart/form-data"

    openapi_request = PyramidOpenAPIRequestFactory.create(pyramid_request)

    assert openapi_request.body == {"key1": "value1", "key2": ["value2.1", "value2.2"]}


def test_no_matched_route() -> None:
    """Test path_pattern when no route is matched."""
    pyramid_request = DummyRequest(path="/foo")
    pyramid_request.matched_route = None
    pyramid_request.content_type = "text/html"

    openapi_request = PyramidOpenAPIRequestFactory.create(pyramid_request)
    assert openapi_request.full_url_pattern == "http://example.com/foo"


def test_mapped_values_response() -> None:
    """Test that values are correctly mapped from pyramid's Response."""
    pyramid_request = DummyRequest()

    assert pyramid_request.response.body == b""
    assert pyramid_request.response.status_code == 200
    assert pyramid_request.response.content_type == "text/html"

    openapi_response = PyramidOpenAPIResponseFactory.create(pyramid_request.response)

    assert openapi_response.data == b""
    assert openapi_response.status_code == 200
    assert openapi_response.mimetype == "text/html"
