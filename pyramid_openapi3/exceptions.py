"""Exceptions used in pyramid_openapi3."""

from openapi_core.schema.exceptions import OpenAPIError
from openapi_core.unmarshalling.schemas.exceptions import InvalidSchemaFormatValue
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.request import Request

import attr
import typing as t


class RequestValidationError(HTTPBadRequest):

    explanation = "Request validation failed."

    def __init__(self, *args, errors: t.List[Exception], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.errors = errors
        self.detail = self.message = "\n".join(str(e) for e in errors)

    def __str__(self) -> str:
        """Return str(self.detail) or self.explanation."""
        return str(self.detail) if self.detail else self.explanation


class ResponseValidationError(HTTPInternalServerError):

    explanation = "Response validation failed."

    def __init__(self, *args, response, errors, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.response = response
        self.errors = errors
        self.detail = self.message = "\n".join(str(e) for e in errors)

    def __str__(self) -> str:
        """Return str(self.detail) or self.explanation."""
        return str(self.detail) if self.detail else self.explanation


@attr.s(hash=True)
class InvalidCustomFormatterValue(InvalidSchemaFormatValue):
    """Value failed to format with a custom formatter."""

    field = attr.ib()

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
        if getattr(err, "schema_errors", None) is not None:
            yield from extract_errors(request, err.schema_errors)
            continue

        output = {"exception": err.__class__.__name__}

        if getattr(err, "message", None) is not None:
            message = err.message
        else:
            message = str(err)

        output.update({"message": message})

        field = None
        if getattr(err, "field", None) is not None:
            field = err.field
        elif getattr(err, "name", None) is not None:
            field = err.name
        elif (
            getattr(err, "validator", None) is not None and err.validator == "required"
        ):
            field = "/".join(err.validator_value)
        elif (
            getattr(err, "path", None) and err.path[0] and isinstance(err.path[0], str)
        ):
            field = "/".join([str(part) for part in err.path])

        if field:
            output.update({"field": field})

        yield output


class MissingEndpointsError(Exception):
    missing: list

    def __init__(self, missing: t.List[str]) -> None:
        self.missing = missing
        message = f"Unable to find routes for endpoints: {', '.join(missing)}"
        super(MissingEndpointsError, self).__init__(message)
