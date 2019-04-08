"""Tests for the wrappers.py module."""


def test_host_url(dummy_openapi_request):
    """No idea what this test does."""
    assert dummy_openapi_request.request.host_url == "http://example.com"
