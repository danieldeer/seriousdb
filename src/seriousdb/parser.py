import json

from .cache import JsonValue


def parse_value(value: str) -> JsonValue:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
