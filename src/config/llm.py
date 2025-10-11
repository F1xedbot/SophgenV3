from typing import Optional
from utils.enum import LLMProvider

class LLMKeyManager:
    def __init__(self):
        self.keys: dict[LLMProvider, list[Optional[str]]] = {}

    def get_key(self, provider: LLMProvider, index: int = 0) -> str:
        keys = self.keys.get(provider)
        if not keys or index >= len(keys):
            raise ValueError(f"No API key available for provider {provider}")
        key = keys[index]
        if not key:
            raise ValueError(f"API key at index {index} for {provider} is not set")
        return key


class LLMConfig:
    def __init__(
        self,
        model_name: str,
        provider: LLMProvider,
        key_manager: LLMKeyManager,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        self.model_name = model_name
        self.provider = provider
        self.key_manager = key_manager
        self.temperature = temperature
        self.max_tokens = max_tokens

    @property
    def api_key(self) -> str:
        return self.key_manager.get_key(self.provider)
