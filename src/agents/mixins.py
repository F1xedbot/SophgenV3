import logging
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional
from google.api_core.exceptions import ResourceExhausted, PermissionDenied
from openai import RateLimitError, AuthenticationError
from langchain_core.messages import HumanMessage, AnyMessage, AIMessage


from manager.llm import LLMKeyManager
from utils.enums import LLMProvider

logger = logging.getLogger(__name__)


class AgentRetryMixin(ABC):
    """
    Mixin that adds safe retry behavior for async agent invocations
    with automatic LLM key rotation on quota/auth failures.
    """

    @abstractmethod
    def _build_agent(self) -> Any:
        """Rebuild or rebind the agent object (e.g., self.agent)."""
        raise NotImplementedError

    @abstractmethod
    def _rebuild_client(self, new_key: str) -> None:
        """Reinitialize the underlying LLM client with a new key."""
        raise NotImplementedError
    
    def all_critical_tools_called(messages: list[AnyMessage], tool_names: list[str]) -> tuple[bool, Optional[HumanMessage]]:
        """
        Checks if all specified critical tools were called with non-empty arguments
        in the last agent turn. Returns a tuple of (success, corrective_message).

        Args:
            messages: List of messages from the agent.
            tool_names: List of critical tool names to check for.
        """
        called_tools = set()

        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.tool_calls:
                for tool_call in message.tool_calls:
                    name = tool_call.get("name")
                    args = tool_call.get("args") or {}
                    if name in tool_names and args:
                        called_tools.add(name)

        missing_tools = [t for t in tool_names if t not in called_tools]
        if not missing_tools:
            return True, None

        # Generate adaptive corrective message for all missing tools
        missing_str = ", ".join(f"'{t}'" for t in missing_tools)
        corrective_message = HumanMessage(
            content=(
                f"CRITICAL FAILURE: You did not call the following critical tools as instructed: {missing_str}. "
                f"Review your instructions and call them immediately."
            )
        )
        return False, corrective_message

    async def safe_invoke(
        self,
        invoke_fn: Callable[..., Awaitable[Any]],
        provider: LLMProvider,
        key_manager: LLMKeyManager,
        max_retries: int = 1,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Safely invoke an async agent call with LLM key rotation retry.

        Args:
            invoke_fn: The async function to invoke (e.g., self.agent.ainvoke)
            provider: LLM provider for key rotation
            key_manager: LLMKeyManager instance
            max_retries: Number of retry attempts on quota/auth failures
            *args, **kwargs: Passed to invoke_fn
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                return await invoke_fn(*args, **kwargs)

            except (RateLimitError, ResourceExhausted) as e:
                logger.warning(f"[QuotaError] {e}. Retrying with new key...")
            except (AuthenticationError, PermissionDenied) as e:
                logger.warning(f"[AuthError] {e}. Retrying with new key...")
            except Exception as e:
                # Non-retryable errors: bubble up immediately
                raise e

            # Rotate API key and rebuild client/agent
            new_key = key_manager.rotate_key(provider)
            if not new_key:
                raise RuntimeError(f"All API keys exhausted for provider: {provider}")

            self._rebuild_client(new_key)
            attempt += 1

        raise RuntimeError(f"Failed after {max_retries + 1} attempts for {provider}.")