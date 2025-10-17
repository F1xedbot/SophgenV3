import hashlib
import json

def hash_data(data: dict, excluded_keys: list[str] | None = [], length: int = 16) -> str:
    filtered_data = {k: v for k, v in data.items() if k not in excluded_keys}
    data_str = json.dumps(filtered_data, sort_keys=True)
    full_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
    return full_hash[:length]
