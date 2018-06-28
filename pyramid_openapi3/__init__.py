from string import Template

from openapi_core import create_spec
from openapi_core.shortcuts import RequestValidator, ResponseValidator
from openapi_spec_validator import validate_spec
from openapi_spec_validator.schemas import read_yaml_file
from pyramid.exceptions import ConfigurationError
from pyramid.config import PHASE0_CONFIG
from pyramid.path import AssetResolver
from pyramid.response import Response, FileResponse

from .wrappers import PyramidOpenAPIRequest, PyramidOpenAPIResponse


def includeme(config):
    config.add_view_deriver(openapi_view)
    config.add_directive("pyramid_openapi3_add_explorer", add_explorer_view)
    config.add_directive("pyramid_openapi3_spec", add_spec_view)

def openapi_view(view, info):
    """ View deriver that takes care of request/response validation.

    If `openapi=True` is passed to `@view_config`, this decorator will:

    - validate request and submit results into request.openali_validated
    - validate response and raise an Exception if errors are found
    """
    if info.options.get('openapi'):
        def wrapper_view(context, request):
            # Validate request and attach all findings for view to introspect
            settings = request.registry.settings['pyramid_openapi3']
            open_request = PyramidOpenAPIRequest(request)
            request.openapi_validated = settings['request_validator'].validate(open_request)

            # Do the view
            response = view(context, request)

            # Validate response and raise if an error is found
            open_response = PyramidOpenAPIResponse(response)
            result = settings['response_validator'].validate(request=open_request, response=open_response)
            result.raise_for_errors()

            return response
        return wrapper_view
    return view

openapi_view.options = ('openapi',)

def add_explorer_view(
    config,
    route='/docs/',
    route_name='pyramid_openapi3.explorer',
    template='static/index.html',
    ui_version='3.17.1',
    ):
    """ Serves Swagger UI at `route` url path.

        :param route: URL path where to serve
        :param route_name: Route name that's being added
        :param template: Dotted path to the html template that renders Swagger UI response
        :param ui_version: Swagger UI version string

    """
    def register():
        resolved_template = AssetResolver().resolve(template)
        def explorer_view(request):
            settings = config.registry.settings
            if settings.get('pyramid_openapi3') is None:
                ConfigurationError('You need to call config.pyramid_openapi3_spec for explorer to work.')
            with open(resolved_template.abspath()) as f:
                template = Template(f.read())
                html = template.safe_substitute(
                    ui_version=ui_version,
                    spec_url=request.route_url(settings['pyramid_openapi3']["spec_route_name"]),
                )
            return Response(html)
        config.add_view(route_name=route_name, view=explorer_view)
        config.add_route(route_name, route)
    config.action(('pyramid_openapi3_add_explorer',), register, order=PHASE0_CONFIG)

def add_spec_view(
    config,
    filepath,
    route='/openapi.yaml',
    route_name='pyramid_openapi3.spec',
    ):
    """ Serves and registers OpenApi 3.0 specification file.

        :param filepath: absolute/relative path to the specification file
        :param route: URL path where to serve specification file
        :param route_name: Route name under which specification file will be served

    """
    def register():
        spec_dict = read_yaml_file(filepath)

        validate_spec(spec_dict)
        spec = create_spec(spec_dict)

        def spec_view(request):
            return FileResponse(
                filepath,
                request=request,
                content_type='text/yaml'
            )
        config.add_view(route_name=route_name, view=spec_view)
        config.add_route(route_name, route)

        config.registry.settings['pyramid_openapi3'] = {
           "filepath": filepath,
           "spec_route_name": route_name,
           "spec": spec,
           "request_validator": RequestValidator(spec),
           "response_validator": ResponseValidator(spec),
        }
    config.action(('pyramid_openapi3_spec',), register, order=PHASE0_CONFIG)
