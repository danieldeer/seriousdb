"""Application-specific exceptions."""


class ApplicationError(Exception):
    """Base class for expected application errors.

    Subclasses declare the HTTP status code and the machine readable error
    code that the API layer uses when building a response.

    Parameters
    ----------
    detail : str, optional
        Human readable description of the error. Defaults to
        `default_detail`.

    Attributes
    ----------
    status_code : int
        HTTP status code of the error response.
    error_code : str
        Machine readable error code of the error response.
    default_detail : str
        Detail used when none is given.
    detail : str
        Human readable description of this error.
    """

    default_detail: str = "An unexpected application error occurred"

    def __init__(self, detail: str | None = None):
        self.detail = detail if detail is not None else self.default_detail
        super().__init__(self.detail)


class ResourceNotFoundError(ApplicationError):
    """A requested resource does not exist."""

    default_detail = "The requested resource was not found"


class ServiceUnavailableError(ApplicationError):
    """A dependency the application needs is currently not usable."""

    default_detail = "The service is temporarily unavailable"
