from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Any

class BaseLLM(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        stream: bool = False,
        tools: List[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None] | Dict[str, Any]:
        """
        Send a chat completion request to the LLM provider.
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the text.
        """
        pass
