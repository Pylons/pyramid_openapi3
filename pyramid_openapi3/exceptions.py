"""Exceptions used in pyramid_openapi3."""

from openapi_core.schema.exceptions import OpenAPIError
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPInternalServerError

import typing as t


class RequestValidationError(HTTPBadRequest):

    explanation = "Request validation failed."

    def __init__(self, *args, errors, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.errors = errors
        self.detail = self.message = "\n".join(str(e) for e in errors)

    def __str__(self) -> str:
        """Return str(self.detail) or self.explanation."""
        return str(self.detail) if self.detail else self.explanation


class ResponseValidationError(HTTPInternalServerError):

    explanation = "Response validation failed."

    def __init__(self, *args, errors, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.errors = errors
        self.detail = self.message = "\n".join(str(e) for e in errors)

    def __str__(self) -> str:
        """Return str(self.detail) or self.explanation."""
        return str(self.detail) if self.detail else self.explanation


def extract_error(err: OpenAPIError) -> t.Dict[str, str]:
    """Extract error's JSON response.

    You can tell pyramid_openapi3 to use your own version of this
    function by providing a dotted-name to your function in
    `request.registry.settings["pyramid_openapi3_extract_error"]`.

    This function expects the below definition in openapi.yaml
    file. If your openapi.yaml is different, you have to
    provide your own extract_error() function.

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
    if getattr(err, "schema_errors", None) is not None:
        for schema_error in err.schema_errors:  # pragma: no branch
            return extract_error(schema_error)

    output = {"exception": err.__class__.__name__}

    if getattr(err, "message", None) is not None:
        message = err.message
    else:
        message = str(err)

    output.update({"message": message})

    field = None
    if getattr(err, "name", None) is not None:
        field = err.name
    elif getattr(err, "validator", None) is not None and err.validator == "required":
        field = "/".join(err.validator_value)
    elif getattr(err, "path", None) and err.path[0]:
        field = "/".join(err.path)
    elif getattr(err, "relative_schema_path", None):
        field = "/".join(err.relative_schema_path)

    if field:
        output.update({"field": field})

    return output
