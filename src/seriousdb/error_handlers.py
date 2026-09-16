"""Centralized FastAPI exception handlers.

All error responses produced by the application share the same structure::

    {"detail": <human readable message>, "error": <machine readable code>}

Expected errors are raised as :class:`~seriousdb.exceptions.ApplicationError`
subclasses by the service and domain layers and translated here. Unexpected
errors are reported to the client as a generic ``500`` response so that no
internal detail leaks out.
"""

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import ApplicationError

INTERNAL_ERROR_DETAIL = "An internal server error occurred"


def error_response(
    status_code: int,
    detail,
    error_code: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build an error response in the application's standard structure."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error": error_code},
        headers=headers,
    )


async def handle_application_error(
    request: Request, exc: ApplicationError
) -> JSONResponse:
    return error_response(exc.status_code, exc.detail, exc.error_code)


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Keep responses consistent for HTTP errors raised by FastAPI itself."""
    try:
        error_code = HTTPStatus(exc.status_code).name.lower()
    except ValueError:
        error_code = "http_error"
    return error_response(
        exc.status_code,
        exc.detail,
        error_code,
        headers=getattr(exc, "headers", None),
    )


async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        exc.errors(),
        "request_validation_error",
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        INTERNAL_ERROR_DETAIL,
        "internal_server_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the centralized handlers on a FastAPI application."""
    app.add_exception_handler(ApplicationError, handle_application_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
