from typing import Optional, List
from utils.enum import LLMProvider

class LLMKeyManager:
    """
    Manages API keys for different providers.
    """
    def __init__(self):
        self.keys: dict[LLMProvider, List[Optional[str]]] = {}

    def get_key(self, provider: LLMProvider, index: int = 0) -> str:
        keys = self.keys.get(provider)
        if not keys or index >= len(keys):
            raise ValueError(f"No API key available for provider {provider}")
        key = keys[index]
        if not key:
            raise ValueError(f"API key at index {index} for {provider} is not set")
        return key