import anthropic
from typing import AsyncGenerator, Dict, List, Any
from app.core.config import settings
from app.services.llm.base import BaseLLM
import json

class AnthropicProvider(BaseLLM):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        stream: bool = False,
        tools: List[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        system_prompt = None
        filtered_messages = []
        
        # Extract system prompt as Anthropic handles it separately
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append({"role": msg["role"], "content": msg["content"]})

        kwargs = {
            "model": model,
            "messages": filtered_messages,
            "temperature": temperature,
            "max_tokens": 4096,
            "stream": True,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt

        # TODO: Implement Tool Calling for Anthropic
        # if tools:
        #    kwargs["tools"] = convert_tools_to_anthropic_format(tools)

        async with self.client.messages.stream(**kwargs) as stream:
             async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield {"type": "content", "content": event.delta.text}
                elif event.type == "message_stop":
                     # Usage tracking if available
                     pass
                # Map other events as needed

    def count_tokens(self, text: str) -> int:
        # Anthropic token counting approximation or client method
        return len(text) // 4 # Rough approximation
