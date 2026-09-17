"""String-to-JSON parsing utilities for seriousdb.

This module exposes a single helper, :func:`parse_value`, used by the
request handlers in :mod:`seriousdb.main` to coerce raw query-string values
into their most specific JSON type before they are written to the cache.

Conversion rules
----------------
- Valid JSON literals (``true``, ``false``, ``null``) become their Python
  equivalents (``True``, ``False``, ``None``).
- JSON numbers become :class:`int` or :class:`float`.
- JSON arrays and objects become :class:`list` and :class:`dict`.
- Anything that is not valid JSON is kept as a plain :class:`str`.
"""

import json

from .cache import JsonValue


def parse_value(value: str) -> JsonValue:
    """Parse a string into a JSON value.

    Attempts to deserialise `value` as JSON. If that fails, the raw string
    is returned as-is, so plain strings like ``"hello"`` are always valid.

    Parameters
    ----------
    value : str
        The raw string to parse.

    Returns
    -------
    JsonValue
        The parsed JSON value, or the original string if parsing fails.
    """
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
