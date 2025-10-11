from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from utils.enum import LLMProvider

class LLMService:
    def __init__(self, model_name: str, api_key: str, provider: LLMProvider | None = LLMProvider.GOOGLE):
        """
        Initialize an LLM service wrapper that can use either OpenAI or Google Generative AI.
        """

        self.model_name = model_name
        self.api_key = api_key
        self.provider = provider.lower()

        if self.provider == LLMProvider.OPENAI:
            self.client = ChatOpenAI(model=model_name, api_key=api_key)
        elif self.provider == LLMProvider.GOOGLE:
            self.client = ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.name = f"{self.provider}:{self.model_name}"

    def generate(self, messages: list[dict], **kwargs):
        """
        Generate a response from the model.
        Args:
            messages: A list of message dicts (e.g., [{"role": "user", "content": "Hello"}])
            kwargs: Additional parameters for model call.
        """
        response = self.client.invoke(messages, **kwargs)
        return response.content if hasattr(response, "content") else response


# Example usage
# if __name__ == "__main__":
#     llm = LLMService(model_name="gpt-4-turbo", api_key="your-openai-key", provider="openai")
#     reply = llm.generate([{"role": "user", "content": "Hello, how are you?"}])
#     print(reply)
