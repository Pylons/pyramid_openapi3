"""Exceptions used in pyramid_openapi3."""

from dataclasses import dataclass
from openapi_core.exceptions import OpenAPIError
from openapi_core.unmarshalling.schemas.exceptions import InvalidSchemaFormatValue
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.request import Request
from pyramid.response import Response

import typing as t


class RequestValidationError(HTTPBadRequest):

    explanation = "Request validation failed."

    def __init__(
        self, *args: t.Any, errors: t.List[Exception], **kwargs: t.Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.errors = errors
        self.detail = self.message = "\n".join(str(e) for e in errors)

    def __str__(self) -> str:
        """Return str(self.detail) or self.explanation."""
        return str(self.detail) if self.detail else self.explanation


class ResponseValidationError(HTTPInternalServerError):

    explanation = "Response validation failed."

    def __init__(
        self,
        *args: t.Any,
        response: Response,
        errors: t.List[Exception],
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.response = response
        self.errors = errors
        self.detail = self.message = "\n".join(str(e) for e in errors)

    def __str__(self) -> str:
        """Return str(self.detail) or self.explanation."""
        return str(self.detail) if self.detail else self.explanation


@dataclass
class InvalidCustomFormatterValue(InvalidSchemaFormatValue):
    """Value failed to format with a custom formatter."""

    field: str

    def __str__(self) -> str:
        """Provide more control over error message."""
        return str(self.original_exception)


class ImproperAPISpecificationWarning(UserWarning):
    """A warning that an end-user's API specification has a problem."""


def extract_errors(
    request: Request, errors: t.List[OpenAPIError]
) -> t.Iterator[t.Dict[str, str]]:
    """Extract errors for JSON response.

    You can tell pyramid_openapi3 to use your own version of this
    function by providing a dotted-name to your function in
    `request.registry.settings["pyramid_openapi3_extract_errors"]`.

    This function expects the below definition in openapi.yaml
    file. If your openapi.yaml is different, you have to
    provide your own extract_errors() function.

    ```
    components:

      schemas:

        Error:
          type: object
          required:
            - exception
            - message
          properties:
            field:
              type: string
            message:
              type: string
            exception:
              type: string

      responses:

        ValidationError:
          description: OpenAPI request/response validation failed
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Error"
    ```
    """
    for err in errors:
        schema_errors = getattr(err, "schema_errors", None)
        if schema_errors is not None:
            yield from extract_errors(request, schema_errors)
            continue

        output = {"exception": err.__class__.__name__}

        message = getattr(err, "message", None)
        if message is None:
            message = str(err)

        output.update({"message": message})

        field = getattr(err, "field", None)
        if field is None:
            field = getattr(err, "name", None)
        if field is None and getattr(err, "validator", None) == "required":
            field = "/".join(getattr(err, "validator_value", []))
        if field is None:
            path = getattr(err, "path", None)
            if path and path[0] and isinstance(path[0], str):
                field = "/".join([str(part) for part in path])

        if field:
            output.update({"field": field})

        yield output


class MissingEndpointsError(Exception):
    missing: list

    def __init__(self, missing: t.List[str]) -> None:
        self.missing = missing
        message = f"Unable to find routes for endpoints: {', '.join(missing)}"
        super(MissingEndpointsError, self).__init__(message)
