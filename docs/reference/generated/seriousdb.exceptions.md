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

### *exception* DiskManagerError(detail=None)

Bases: [`ApplicationError`](#seriousdb.exceptions.ApplicationError)

A raw page read, write or allocation on the database file failed.

### *exception* ResourceNotFoundError(detail=None)

Bases: [`ApplicationError`](#seriousdb.exceptions.ApplicationError)

A requested resource does not exist.

### *exception* SerializationError(detail=None)

Bases: [`ApplicationError`](#seriousdb.exceptions.ApplicationError)

A storage page cannot be serialized or deserialized.

### *exception* ServiceUnavailableError(detail=None)

Bases: [`ApplicationError`](#seriousdb.exceptions.ApplicationError)

A dependency the application needs is currently not usable.
