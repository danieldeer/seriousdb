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
    """Build an error response in the application's standard structure.

    Parameters
    ----------
    status_code : int
        HTTP status code of the response.
    detail : Any
        Human readable description of the error. Must be JSON serializable.
    error_code : str
        Machine readable error code.
    headers : dict of str to str, optional
        Extra headers to send with the response.

    Returns
    -------
    JSONResponse
        Response with the body ``{"detail": detail, "error": error_code}``.
    """
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error": error_code},
        headers=headers,
    )


async def handle_application_error(
    request: Request, exc: ApplicationError
) -> JSONResponse:
    """Translate an :class:`ApplicationError` into its error response.

    Parameters
    ----------
    request : Request
        The request that raised the error.
    exc : ApplicationError
        The raised error.

    Returns
    -------
    JSONResponse
        Response with the status code, detail and error code of `exc`.
    """
    return error_response(exc.status_code, exc.detail, exc.error_code)


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Keep responses consistent for HTTP errors raised by FastAPI itself.

    The error code is the lowercase name of the status code, for example
    ``not_found``, or ``http_error`` for non-standard status codes.

    Parameters
    ----------
    request : Request
        The request that raised the error.
    exc : starlette.exceptions.HTTPException
        The raised error.

    Returns
    -------
    JSONResponse
        Response with the status code, detail and headers of `exc`.
    """
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
    """Translate invalid request parameters into a ``422`` response.

    Parameters
    ----------
    request : Request
        The request that failed validation.
    exc : RequestValidationError
        The validation error.

    Returns
    -------
    JSONResponse
        ``422`` response with error code ``request_validation_error`` and the
        list of validation problems as detail.
    """
    return error_response(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        exc.errors(),
        "request_validation_error",
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Report an unexpected error as a generic ``500`` response.

    No information about `exc` is included in the response.

    Parameters
    ----------
    request : Request
        The request that raised the error.
    exc : Exception
        The raised error.

    Returns
    -------
    JSONResponse
        ``500`` response with error code ``internal_server_error``.
    """
    return error_response(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        INTERNAL_ERROR_DETAIL,
        "internal_server_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the centralized handlers on a FastAPI application.

    Parameters
    ----------
    app : FastAPI
        Application to register the handlers on. It is modified in place.
    """
    app.exception_handler(ApplicationError)(handle_application_error)
    app.exception_handler(StarletteHTTPException)(handle_http_exception)
    app.exception_handler(RequestValidationError)(handle_request_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
