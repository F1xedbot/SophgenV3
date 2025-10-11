from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from config.registry import LLM_REGISTRY, LLMConfig
from utils.enum import LLMProvider

class LLMService:
    """
    Wrapper around LLM clients (OpenAI / Google) for simplified usage.
    Automatically finds config by model name.
    """
    def __init__(self, model_name: str):
        self.config: LLMConfig = self._find_config(model_name)
        self.client = self._init_client()

    def _find_config(self, model_name: str) -> LLMConfig:
        if model_name not in LLM_REGISTRY:
            raise ValueError(f"LLM config not found for model: {model_name}")
        return LLM_REGISTRY[model_name]

    def _init_client(self):
        if self.config.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=self.config.model_name,
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        elif self.config.provider == LLMProvider.GOOGLE:
            return ChatGoogleGenerativeAI(
                model=self.config.model_name,
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def generate(self, messages: List[Dict], **kwargs) -> str:
        """
        Simple wrapper to call the LLM.
        """
        response = self.client.invoke(messages, **kwargs)
        return getattr(response, "content", response)
