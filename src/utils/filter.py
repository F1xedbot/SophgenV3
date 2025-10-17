import orjson
from typing import Iterable, Mapping, Any

def filter_dict_fields(
    keys: Iterable[str], 
    data: Mapping[str, Any], 
    fields: Iterable[str], 
    prefix: str = "research:"
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
