"""Application-specific exceptions."""


class ApplicationError(Exception):
    """Base class for expected application errors.

    Parameters
    ----------
    detail : str, optional
        Human readable description of the error. Defaults to
        `default_detail`.

    Attributes
    ----------
    default_detail : str
        Detail used when none is given.
    detail : str
        Human readable description of this error.
    """

    default_detail: str = "An unexpected application error occurred"

    def __init__(self, detail: str | None = None):
        self.detail = detail if detail is not None else self.default_detail
        super().__init__(self.detail)


class SerializationError(ApplicationError):
    """A storage page cannot be serialized or deserialized."""

    default_detail = "The storage page could not be serialized or deserialized"


class ResourceNotFoundError(ApplicationError):
    """A requested resource does not exist."""

    default_detail = "The requested resource was not found"


class ServiceUnavailableError(ApplicationError):
    """A dependency the application needs is currently not usable."""

    default_detail = "The service is temporarily unavailable"


class DiskManagerError(ApplicationError):
    """A raw page read, write or allocation on the database file failed."""

    default_detail = "The database file could not be accessed as fixed-size pages"
