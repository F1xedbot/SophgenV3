from typing import Optional, List
from utils.enums import LLMProvider
from utils.const import FIRST_KEY_INDEX
import logging

logger = logging.getLogger(__name__)

class LLMKeyManager:
    """
    Manages API keys for different providers, with automatic key rotation.
    """
    def __init__(self):
        self.keys: dict[LLMProvider, List[Optional[str]]] = {}
        self.current_index: dict[LLMProvider, int] = {}

    def get_key(self, provider: LLMProvider, index: Optional[int] = None) -> str:
        keys = self.keys.get(provider)
        if not keys:
            raise ValueError(f"No API key available for provider {provider}")

        i = index if index is not None else self.current_index.get(provider, FIRST_KEY_INDEX)
        if i >= len(keys):
            raise ValueError(f"No more API keys left for provider {provider}")

        key = keys[i]
        if not key:
            raise ValueError(f"API key at index {i} for {provider} is not set")
        return key

    def rotate_key(self, provider: LLMProvider) -> Optional[str]:
        """Move to the next API key for a provider, if available."""
        keys = self.keys.get(provider)
        if not keys:
            raise ValueError(f"No keys found for provider {provider}")

        current = self.current_index.get(provider, FIRST_KEY_INDEX)
        if current + 1 >= len(keys):
            logger.error(f"All API keys exhausted for {provider}.")
            return None

        new_index = current + 1
        self.current_index[provider] = new_index
        new_key = keys[new_index]
        logger.warning(f"Switching to next API key ({new_index + 1}/{len(keys)}) for {provider}.")
        return new_key
