import os
from config.llm import LLMKeyManager, LLMConfig
from utils.enum import LLMProvider, LLMModels
from typing import Dict
from dotenv import load_dotenv
from types import MappingProxyType

load_dotenv()

def load_keys(prefix: str) -> list[str]:
    """Load all non-empty environment variables starting with the given prefix, sorted for consistency."""
    return sorted([v for k, v in os.environ.items() if k.startswith(prefix) and v])

# Initialize key manager
KEY_MANAGER = LLMKeyManager()
KEY_MANAGER.keys = {
    LLMProvider.OPENAI: load_keys("OPENAI"),
    LLMProvider.GOOGLE: load_keys("GOOGLE"),
}

# Validate keys
for provider, keys in KEY_MANAGER.keys.items():
    if not keys:
        raise RuntimeError(f"No API keys found for provider {provider}")

# Initialize registry
LLM_REGISTRY: Dict[str, LLMConfig] = {
    LLMModels.GPT_3_5_TURBO: LLMConfig(LLMModels.GPT_3_5_TURBO, LLMProvider.OPENAI, KEY_MANAGER),
    LLMModels.GPT_4_O_MINI: LLMConfig(LLMModels.GPT_4_O_MINI, LLMProvider.OPENAI, KEY_MANAGER),
    LLMModels.GEMINI_2_5_FLASH_LITE: LLMConfig(LLMModels.GEMINI_2_5_FLASH_LITE, LLMProvider.GOOGLE, KEY_MANAGER),
    LLMModels.GEMINI_2_5_FLASH: LLMConfig(LLMModels.GEMINI_2_5_FLASH, LLMProvider.GOOGLE, KEY_MANAGER),
}

# Make registry immutable
LLM_REGISTRY = MappingProxyType(LLM_REGISTRY)