import math 

def _validate_ttl(ex: float | None) -> None:
    if ex is None:
        return

    if isinstance(ex, bool) or not isinstance(ex, (int, float)):
        raise TypeError("ex must be a number or None")

    if not math.isfinite(ex):
        raise ValueError("ex must be finite")

    if ex <= 0:
        raise ValueError("ex must be greater than 0")