"""Tests validation of openapi responses."""

from pyramid.testing import testConfig
from pyramid_openapi3.check_openapi_responses import validate_required_responses
from pyramid_openapi3.exceptions import ResponseValidationError

import pytest
import tempfile
import yaml

VALIDATION_DOCUMENT = b"""
required_responses:
  get:
    - '200'
    - '400'
# Additional required response definitions for endpoints with parameters
required_responses_params:
  get:
    - '404'
"""


def test_get_config_no_file() -> None:
    """Test get_config when config is not a file object."""
    from pyramid_openapi3.check_openapi_responses import get_config

    with pytest.raises(RuntimeError):
        get_config("file_does_not_exist")


def test_response_validation_error() -> None:
    """Test that ResponseValidationError is raised when 404 is missing."""

    SPEC_DOCUMENT = b"""
        openapi: "3.0.0"
        info:
          version: "1.0.0"
          title: Foo API
        paths:
          /foo:
            get:
              parameters:
              - name: bar
                in: query
                schema:
                  type: integer
              responses:
                "200":
                  description: A foo
                "400":
                  description: Bad Request
    """

    with testConfig() as config:
        config.include("pyramid_openapi3")

        with tempfile.NamedTemporaryFile() as document:
            document.write(VALIDATION_DOCUMENT)
            document.seek(0)

            config.add_settings(pyramid_openapi3_responses_config=document.name)
            with pytest.raises(ResponseValidationError):
                validate_required_responses(yaml.safe_load(SPEC_DOCUMENT), config)


def test_happy_path() -> None:
    """Test validation of openapi responses."""

    SPEC_DOCUMENT = b"""
        openapi: "3.0.0"
        info:
          version: "1.0.0"
          title: Foo API
        paths:
          /foo:
            get:
              parameters:
              - name: bar
                in: query
                schema:
                  type: integer
              responses:
                "200":
                  description: A foo
                "400":
                  description: Bad Request
                "404":
                  description: Not Found
    """

    with testConfig() as config:
        config.include("pyramid_openapi3")

        with tempfile.NamedTemporaryFile() as document:
            document.write(VALIDATION_DOCUMENT)
            document.seek(0)

            config.add_settings(pyramid_openapi3_responses_config=document.name)
            validate_required_responses(yaml.safe_load(SPEC_DOCUMENT), config)


def test_no_params() -> None:
    """Test spec without parameters."""

    SPEC_DOCUMENT = b"""
        openapi: "3.0.0"
        info:
          version: "1.0.0"
          title: Foo API
        paths:
          /foo:
            get:
              responses:
                "200":
                  description: A foo
                "400":
                  description: Bad Request
                "404":
                  description: Not Found
    """

    with testConfig() as config:
        config.include("pyramid_openapi3")

        with tempfile.NamedTemporaryFile() as document:
            document.write(VALIDATION_DOCUMENT)
            document.seek(0)

            config.add_settings(pyramid_openapi3_responses_config=document.name)
            validate_required_responses(yaml.safe_load(SPEC_DOCUMENT), config)
