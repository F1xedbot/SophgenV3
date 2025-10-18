import orjson
from typing import Iterable, Mapping, Any

def filter_dict_fields(
    keys: Iterable[str], 
    data: Mapping[str, Any], 
    fields: Iterable[str], 
    prefix: str = ""
) -> str:
    """
    Filters a dictionary based on a list of keys and specified fields.

    Args:
        keys: Iterable of IDs (e.g., CWE IDs).
        data: Dictionary containing detailed entries.
        fields: List of fields to keep from each entry.
        prefix: Optional prefix for keys in the dictionary.

    Returns:
        JSON string of the filtered entries.
    """
    filtered_list = []
    for k in keys:
        key = f"{prefix}{k.strip()}"
        value = data.get(key)
        if not value:
            continue
        filtered = {field: value.get(field) for field in fields}
        filtered_list.append(filtered)

    return orjson.dumps(filtered_list, option=orjson.OPT_INDENT_2).decode("utf-8")

def filter_list_fields(
    keys: Iterable[str],
    data: list[dict[str, Any]],
    fields: Iterable[str],
    key_field: str = "id"
) -> dict:
    """
    Filters a list of dictionaries based on a list of keys and specified fields.

    Args:
        keys: Iterable of keys to match (e.g., CWE IDs).
        data: List of dictionaries containing detailed entries.
        fields: List of fields to keep from each entry.
        key_field: The field in each dictionary to compare against keys.

    Returns:
        JSON string of the filtered entries.
    """
    keys_set = {str(k).strip() for k in keys}  # faster lookup O(1)
    filtered_list = []

    for entry in data:
        entry_key = str(entry.get(key_field, "")).strip()
        if entry_key in keys_set:
            filtered = {field: entry.get(field) for field in fields}
            filtered_list.append(filtered)

    return filtered_list