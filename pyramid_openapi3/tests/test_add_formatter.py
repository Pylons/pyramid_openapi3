"""Tests for registering custom formatters."""

from pyramid.testing import DummyRequest
from pyramid.testing import testConfig


def test_add_formatter() -> None:
    """Test registration of a custom formatter."""

    with testConfig() as config:
        request = DummyRequest()

        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_formatter("foormatter", lambda x: x)

        formatter = request.registry.settings["pyramid_openapi3_formatters"].get(
            "foormatter", None
        )
        assert formatter("foo") == "foo"
