# seriousdb.exceptions

Application-specific exceptions.

### Exceptions

### *exception* ApplicationError(detail=None)

Bases: `Exception`

Base class for expected application errors.

* **Parameters:**
  **detail** (*str* *,* *optional*) – Human readable description of the error. Defaults to default_detail.
* **Variables:**
  * **default_detail** (*str*) – Detail used when none is given.
  * **detail** (*str*) – Human readable description of this error.

### *exception* CorruptDatabaseError(detail=None)

Bases: [`ApplicationError`](#seriousdb.exceptions.ApplicationError)

A corrupt database was encountered.

### *exception* ResourceNotFoundError(detail=None)

Bases: [`ApplicationError`](#seriousdb.exceptions.ApplicationError)

A requested resource does not exist.

### *exception* ServiceUnavailableError(detail=None)

Bases: [`ApplicationError`](#seriousdb.exceptions.ApplicationError)

A dependency the application needs is currently not usable.
