"""A Todo-app implementation using pyramid_openapi3."""

from dataclasses import dataclass
from openapi_core.schema.exceptions import OpenAPIError
from openapi_core.schema.exceptions import OpenAPIMappingError
from pyramid.config import Configurator
from pyramid.httpexceptions import exception_response
from pyramid.httpexceptions import HTTPException
from pyramid.request import Request
from pyramid.view import exception_view_config
from pyramid.view import view_config
from pyramid_openapi3.exceptions import RequestValidationError
from wsgiref.simple_server import make_server

import os
import typing as t


@dataclass
class Item:
    """A single TODO item."""

    title: str

    def __json__(self, request: Request) -> t.Dict["str", "str"]:
        """JSON-renderer for this object."""
        return {"title": self.title}


# fmt: off
# Poor-man's in-memory database. Pre-populated with three TODO items.
ITEMS = [
    Item(title="Buy milk"),
    Item(title="Buy eggs"),
    Item(title="Make pankaces!"),
]
# fmt: on


@view_config(route_name="todo", renderer="json", request_method="GET", openapi=True)
def get(request: Request) -> t.List[Item]:
    """Serve the list of TODO items for GET requests."""
    return ITEMS


@view_config(route_name="todo", renderer="json", request_method="POST", openapi=True)
def post(request: Request) -> t.List[t.Dict["str", "str"]]:
    """Handle POST requests and create TODO items."""
    item = Item(title=request.openapi_validated.body.title)
    ITEMS.append(item)
    return "Item added."


@exception_view_config(RequestValidationError, renderer="json")
def openapi_validation_error(
    context: HTTPException, request: Request
) -> exception_response:
    """If there are errors when handling the request, return them as response."""
    errors = [extract_error(err) for err in context.errors]
    return exception_response(400, json_body=errors)


def extract_error(err: OpenAPIError) -> t.Dict[str, str]:
    """Extract error JSON response using an Exception instance."""
    output = {"message": str(err), "exception": err.__class__.__name__}
    field_name = None

    if isinstance(getattr(err, "original_exception", None), OpenAPIMappingError):
        return extract_error(err.original_exception)
    if getattr(err, "schema_errors", []):
        for schema_error in err.schema_errors:
            return extract_error(schema_error)
    if getattr(err, "message", None) is not None:
        output["message"] = err.message
    if getattr(err, "absolute_path", []):
        field_name = err.absolute_path.pop()

    if field_name is not None:
        output.update({"field": field_name})

    return output


def app():
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(
            os.path.join(os.path.dirname(__file__), "openapi.yaml")
        )
        config.pyramid_openapi3_add_explorer()
        config.add_route("todo", "/")
        config.scan(".")

        return config.make_wsgi_app()


if __name__ == "__main__":
    """If app.py is called directly, start up the app."""
    print("Swagger UI available at http://0.0.0.0:6543/docs/")  # noqa: T001
    server = make_server("0.0.0.0", 6543, app())
    server.serve_forever()
