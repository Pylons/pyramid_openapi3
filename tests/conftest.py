"""Various py.test fixtures."""

from pyramid.testing import DummyRequest
from pytest import fixture


@fixture
def dummy_openapi_request():
    """Get pyramid_openapi3-wrapped DummyRequest."""
    from pyramid_openapi3.wrappers import PyramidOpenAPIRequest

    dummy_request = DummyRequest()
    return PyramidOpenAPIRequest(dummy_request)
