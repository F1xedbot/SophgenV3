import os
from config.llm import LLMConfig
from manager.llm import LLMKeyManager
from utils.enums import LLMProvider, LLMModels
from types import MappingProxyType

def load_keys(prefix: str) -> list[str]:
    """Load all non-empty environment variables starting with prefix."""
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

# Initialize immutable registry
LLM_REGISTRY = MappingProxyType({
    # OpenAI
    LLMModels.GPT_3_5_TURBO: LLMConfig(LLMModels.GPT_3_5_TURBO, LLMProvider.OPENAI, KEY_MANAGER),
    LLMModels.GPT_4_O_MINI: LLMConfig(LLMModels.GPT_4_O_MINI, LLMProvider.OPENAI, KEY_MANAGER),
    # Google
    LLMModels.GEMINI_2_5_FLASH_LITE: LLMConfig(LLMModels.GEMINI_2_5_FLASH_LITE, LLMProvider.GOOGLE, KEY_MANAGER),
    LLMModels.GEMINI_2_5_FLASH: LLMConfig(LLMModels.GEMINI_2_5_FLASH, LLMProvider.GOOGLE, KEY_MANAGER),
})