"""Tests for pyramid_openapi3.add_exception_views setting."""

from pyramid.testing import testConfig
from pyramid_openapi3 import openapi_validation_error
from pyramid_openapi3.exceptions import RequestValidationError
from pyramid_openapi3.exceptions import ResponseValidationError


def test_add_exception_views__missing() -> None:
    """Test exception views are created when pyramid_openapi3.add_exception_views setting is missing."""

    with testConfig() as config:
        config.include("pyramid_openapi3")

        views = {
            view["introspectable"]["context"]: view["introspectable"]["callable"]
            for view in config.registry.introspector.get_category("views") or []
        }

        assert views[RequestValidationError] == openapi_validation_error
        assert views[ResponseValidationError] == openapi_validation_error


def test_add_exception_views__true() -> None:
    """Test exception views are created when pyramid_openapi3.add_exception_views setting is True."""

    with testConfig() as config:
        config.registry.settings["pyramid_openapi3.add_exception_views"] = True

        config.include("pyramid_openapi3")

        views = {
            view["introspectable"]["context"]: view["introspectable"]["callable"]
            for view in config.registry.introspector.get_category("views") or []
        }

        assert views[RequestValidationError] == openapi_validation_error
        assert views[ResponseValidationError] == openapi_validation_error


def test_add_exception_views__false() -> None:
    """Test exception views are not created when pyramid_openapi3.add_exception_views setting is False."""

    with testConfig() as config:
        config.registry.settings["pyramid_openapi3.add_exception_views"] = False

        config.include("pyramid_openapi3")

        views = {
            view["introspectable"]["context"]: view["introspectable"]["callable"]
            for view in config.registry.introspector.get_category("views") or []
        }

        assert RequestValidationError not in views
        assert ResponseValidationError not in views
