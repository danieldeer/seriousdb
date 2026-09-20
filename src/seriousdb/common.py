"""Common utilities shared across the SeriousDB package.

This module contains reusable validation and helper functions that are
used by multiple components of the package.
"""

import math


def _validate_ttl(ex: float | None) -> None:
    """Validate a time-to-live (TTL) value.

    Parameters
    ----------
    ex : float | None
        TTL in seconds. ``None`` indicates that the key should not expire.

    Raises
    ------
    TypeError
        If ``ex`` is not an integer, float, or ``None``.
    ValueError
        If ``ex`` is not finite or is less than or equal to zero.
    """
    if ex is None:
        return

    if isinstance(ex, bool) or not isinstance(ex, (int, float)):
        raise TypeError("ex must be a number or None")

    if not math.isfinite(ex):
        raise ValueError("ex must be finite")

    if ex <= 0:
        raise ValueError("ex must be greater than 0")
