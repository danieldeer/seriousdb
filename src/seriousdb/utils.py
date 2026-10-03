from enum import Enum


class ErrorForTypeFile(Enum):
    SDBF = "sdbf"
    SDBWF = "sdbwf"

def get_duplicate_detector(source: ErrorForTypeFile):
    def detect_duplicates(pairs):
        """Detect duplicate keys during JSON parsing and raise an error.

        Used as an `object_pairs_hook` in `json.loads` to prevent duplicate
        keys from being silently overwritten.

        Args:
            pairs (list[tuple[str, Any]]): Key-value pairs extracted from the JSON object.
            source (ErrorForTypeFile): The file type context providing the error template.

        Returns:
            dict: A dictionary containing the validated, unique key-value pairs.

        Raises:
            ValueError: If a duplicate key is detected in the current JSON object.
        """
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError(f"Duplicate occurred in {source.value}: '{k}'")
            d[k] = v
        return d
    return detect_duplicates