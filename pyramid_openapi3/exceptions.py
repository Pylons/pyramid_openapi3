"""Exceptions used in pyramid_openapi3."""
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

    def _json_formatter(self, status, body, title, environ) -> t.Dict:
        return {"message": body, "code": status, "title": self.title}


class ResponseValidationError(HTTPInternalServerError):

    explanation = "Response validation failed."

    def __init__(self, *args, errors, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.errors = errors
        self.detail = self.message = "\n".join(str(e) for e in errors)

    def __str__(self) -> str:
        """Return str(self.detail) or self.explanation."""
        return str(self.detail) if self.detail else self.explanation

    def _json_formatter(self, status, body, title, environ) -> t.Dict:
        return {"message": body, "code": status, "title": self.title}
