"""Tests for registering custom deserializers."""

from pyramid.testing import DummyRequest
from pyramid.testing import testConfig


def test_add_deserializer() -> None:
    """Test registration of a custom deserializer."""

    with testConfig() as config:
        request = DummyRequest()

        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_deserializer("deserializer", lambda x: x)

        deserializer = request.registry.settings["pyramid_openapi3_deserializers"].get(
            "deserializer", None
        )
        assert deserializer("foo") == "foo"
