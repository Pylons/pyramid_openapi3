"""Verify that endpoints have defined required responses."""

from .exceptions import ResponseValidationError
from openapi_core.schema.specs.models import Spec
from pathlib import Path
from pyramid.config import Configurator

import openapi_core
import structlog  # type: ignore
import typing as t
import yaml

logger = structlog.get_logger(__name__)


def get_config(config_path: str) -> t.Dict[str, str]:
    """Read config from file."""
    config = Path(config_path)

    if not config.is_file():
        raise RuntimeError(f"ERROR Config file not found on: {config}\n")

    with config.open("r") as f:
        return yaml.safe_load(f)


def required_responses(
    config: t.Dict, endpoint: str, method: str, has_params: bool
) -> t.Set:
    """Get required responses for given method on endpoint."""
    required_resp: t.Set = set(config.get("required_responses", {}).get(method, []))
    if has_params:
        required_params: set = set(
            config.get("required_responses_params", {}).get(method, [])
        )
        required_resp = required_resp.union(required_params)
    allowed_missing: set = set(
        config.get("allowed_missing_responses", {}).get(endpoint, {}).get(method, [])
    )
    required_resp = required_resp - allowed_missing
    return required_resp


def validate_required_responses(spec_dict: dict, config: Configurator) -> None:
    """Verify that all endpoints have defined required responses."""
    check_failed: bool = False
    missing_responses_count: int = 0
    errors = []

    filepath: str = config.registry.settings.get("pyramid_openapi3_responses_config")
    if not filepath:
        logger.warning(
            "pyramid_openapi3_responses_config not configured. Required Responses will not be validated."
        )
        return

    responses_config: t.Dict[str, str] = get_config(filepath)

    spec: Spec = openapi_core.create_spec(spec_dict)
    for path in spec.paths.values():
        for operation in path.operations.values():
            operation_responses = operation.responses.keys()
            method: str = operation.http_method
            endpoint: str = operation.path_name
            has_params: bool = len(operation.parameters) > 0
            required: t.Set = required_responses(
                responses_config, endpoint, method, has_params
            )

            missing_responses: t.Set = required - operation_responses
            for missing_response in missing_responses:
                check_failed = True
                missing_responses_count += 1
                errors.append(
                    "ERROR missing response "
                    f"'{missing_response}' for '{method}' request on path "
                    f"'{endpoint}'\n"
                )
    if check_failed:
        errors.append(
            "\nFAILED: Openapi responses check: "
            f"{missing_responses_count} missing response definitions. \n"
        )
        raise ResponseValidationError(errors=errors)
