from config.local import LOCAL_CWE_CACHE_PATH
import orjson
import aiofiles
import os
from pathlib import Path

FULL_LOCAL_CWE_CACHE_PATH = Path(__file__).parent / LOCAL_CWE_CACHE_PATH

async def load_local_cache(file_path: str = FULL_LOCAL_CWE_CACHE_PATH) -> dict:
    """
    Asynchronously loads a local JSON cache using orjson.
    Returns an empty dict if file not found or invalid.
    """
    loaded_cache = {}
    try:
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
            loaded_cache = orjson.loads(content)
    except FileNotFoundError:
        loaded_cache = {}
    except orjson.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in cache file: {file_path}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to load local cache: {e}") from e
    finally:
        return loaded_cache


async def read_cache(cache: dict, key: str) -> dict:
    """
    Reads a value from the in-memory cache.
    Falls back to loading from local cache if not found.
    """
    if key in cache:
        return cache[key]

    # fallback to local file cache
    local_cache = await load_local_cache()
    return local_cache.get(key, {})


async def update_cache(cache: dict, key: str, value: dict, file_path: str = FULL_LOCAL_CWE_CACHE_PATH) -> None:
    """
    Updates both the in-memory cache and the local JSON backup file.
    """
    cache[key] = value
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(orjson.dumps(cache, option=orjson.OPT_INDENT_2))
    except Exception as e:
        raise RuntimeError(f"Failed to update local cache: {e}") from e