"""openapi-core wrappers module for pyramid"""

from openapi_core.wrappers.base import BaseOpenAPIRequest, BaseOpenAPIResponse


class PyramidOpenAPIRequest(BaseOpenAPIRequest):

    def __init__(self, request):
        self.request = request

    @property
    def host_url(self):
        return self.request.host_url

    @property
    def path(self):
        return self.request.path

    @property
    def method(self):
        return self.request.method.lower()

    @property
    def path_pattern(self):
        return self.path

    @property
    def parameters(self):
        return {
            'path': self.request.params,
            'query': self.request.query_string,
            'headers': self.request.headers,
            'cookies': self.request.cookies,
        }

    @property
    def body(self):
        return self.request.body

    @property
    def mimetype(self):
        return self.request.content_type


class PyramidOpenAPIResponse(BaseOpenAPIResponse):

    def __init__(self, response):
        self.response = response

    @property
    def data(self):
        return self.response.body

    @property
    def status_code(self):
        return self.response._status_code

    @property
    def mimetype(self):
        return self.response.content_type
