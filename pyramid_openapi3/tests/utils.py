"""Helpers shared by the test modules."""

from dataclasses import dataclass
from pyramid.config import Configurator
from pyramid.interfaces import Interface
from pyramid.interfaces import IRouteRequest
from pyramid.interfaces import IView
from pyramid.interfaces import IViewClassifier
from pyramid.request import apply_request_extensions
from pyramid.testing import DummyRequest

import typing as t


@dataclass
class DummyRoute:
    """Stand-in for the route pyramid sets as request.matched_route."""

    name: str
    pattern: str


class DummyStartResponse:
    """Record what a WSGI app passes to start_response."""

    def __call__(self, status: str, headerlist: list[tuple[str, str]]) -> None:
        """WSGI start_response protocol."""
        self.status = status
        self.headerlist = headerlist


def get_view(config: Configurator, route_name: str) -> t.Callable:
    """Return the view registered for route_name, with all its derivers applied."""
    request_interface = config.registry.queryUtility(IRouteRequest, name=route_name)
    return config.registry.adapters.registered(
        (IViewClassifier, request_interface, Interface), IView, name=""
    )


def make_request(config: Configurator, route_name: str, **kw: t.Any) -> DummyRequest:
    """Return a DummyRequest that matched the route_name route at /route_name."""
    request = DummyRequest(config=config, **kw)
    apply_request_extensions(request)
    request.matched_route = DummyRoute(name=route_name, pattern=f"/{route_name}")
    return request
