from pytest import fixture

from pyramid.testing import DummyRequest


@fixture
def dummy_openapi_request():
    from pyramid_openapi3.wrappers import PyramidOpenAPIRequest
    dummy_request = DummyRequest()
    return PyramidOpenAPIRequest(dummy_request)

def test_host_url(dummy_openapi_request):
    assert dummy_openapi_request.request.host_url == "http://example.com"
