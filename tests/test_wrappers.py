def test_host_url(dummy_openapi_request):
    assert dummy_openapi_request.request.host_url == "http://example.com"
