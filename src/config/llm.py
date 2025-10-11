from typing import Optional
from utils.enum import LLMProvider
from manager.llm import LLMKeyManager

class LLMConfig:
    """
    Immutable configuration for an LLM model.
    """
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
        self._frozen = True

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError("LLMConfig is immutable")
        super().__setattr__(name, value)

    @property
    def api_key(self) -> str:
        return self.key_manager.get_key(self.provider)