"""Tests for registering custom unmarshallers."""

from pyramid.testing import DummyRequest
from pyramid.testing import testConfig


def test_add_unmarshaller() -> None:
    """Test registration of a custom unmarshaller."""

    with testConfig() as config:
        request = DummyRequest()

        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_unmarshaller("unmarshaller", lambda x: x)

        unmarshaller = request.registry.settings["pyramid_openapi3_unmarshallers"].get(
            "unmarshaller", None
        )
        assert unmarshaller("foo") == "foo"
