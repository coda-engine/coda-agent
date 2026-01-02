import google.generativeai as genai
from typing import AsyncGenerator, Dict, List, Any
from app.core.config import settings
from app.services.llm.base import BaseLLM
import json

class GoogleProvider(BaseLLM):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        genai.configure(api_key=self.api_key)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-pro",
        temperature: float = 0.7,
        stream: bool = False,
        tools: List[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        # Convert messages to Gemini format
        # Gemini expects "user" and "model" roles
        gemini_history = []
        last_user_message = ""
        
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]
            if role == "user":
                 last_user_message = content
            # Simplified history handling; typically Gemini uses chat sessions
            if msg["role"] != "system":
                 gemini_history.append({"role": role, "parts": [content]})
        
        # Initialize model
        gemini_model = genai.GenerativeModel(model)

        # Generate (simplified for streaming single turn for now, or use chat session)
        # Using generate_content_async with stream=True
        
        # TODO: Handle full chat history correctly
        # For now, just sending the last user message as prompt (MVP)
        # Real implementation needs to reconstruct ChatSession
        
        response = await gemini_model.generate_content_async(
            last_user_message, 
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature
            )
        )
        
        async for chunk in response:
            if chunk.text:
                yield {"type": "content", "content": chunk.text}

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
