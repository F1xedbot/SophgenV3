import orjson
import aiofiles
import os
from pathlib import Path

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path.cwd()))
FULL_LOCAL_CWE_CACHE_PATH = PROJECT_ROOT / os.environ['CWE_CACHE_PATH']

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


async def read_cache(key: str, file_path: str = FULL_LOCAL_CWE_CACHE_PATH) -> dict:
    """
    Reads a value from local cache.
    """
    local_cache = await load_local_cache(file_path)
    return local_cache.get(key, {})


async def update_cache(key: str, value: dict, file_path: str = FULL_LOCAL_CWE_CACHE_PATH) -> None:
    """
    Updates the local cache.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    local_cache = load_local_cache(file_path)
    local_cache[key] = value
    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(orjson.dumps(local_cache, option=orjson.OPT_INDENT_2))
    except Exception as e:
        raise RuntimeError(f"Failed to update local cache: {e}") from e