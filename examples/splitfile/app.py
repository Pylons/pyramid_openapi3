"""A Todo-app implementation using pyramid_openapi3 and YAML spec split into multiple files.

See README.md at
https://github.com/Pylons/pyramid_openapi3/tree/master/examples/splitfile
"""

from dataclasses import dataclass
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.router import Router
from pyramid.view import view_config
from wsgiref.simple_server import make_server

import os
import typing as t


@dataclass
class Item:
    """A single TODO item."""

    title: str

    def __json__(self, request: Request) -> t.Dict[str, str]:
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
def post(request: Request) -> str:
    """Handle POST requests and create TODO items."""
    item = Item(title=request.openapi_validated.body["title"])
    ITEMS.append(item)
    return "Item added."


def app() -> Router:
    """Prepare a Pyramid app."""
    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.add_static_view(name="spec", path="spec")
        config.pyramid_openapi3_spec_directory(
            os.path.join(os.path.dirname(__file__), "spec/openapi.yaml"),
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
