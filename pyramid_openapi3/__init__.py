from string import Template

from openapi_core import create_spec
from openapi_core.validators import RequestValidator, ResponseValidator
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
            result = settings['response_validator'].validate(open_response)
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
    """"""
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
    """"""
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
