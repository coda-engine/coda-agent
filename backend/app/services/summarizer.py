from typing import List, Optional
from app.models.message import Message
from app.services.llm.openai import OpenAIProvider

class ContextSummarizer:
    def __init__(self):
        self.provider = OpenAIProvider()
        self.model = "gpt-4o" # or gpt-4o-mini for speed/cost

    async def summarize(self, messages: List[Message], current_summary: Optional[str] = None) -> str:
        """
        Generates a summary of the provided messages, incorporating any existing summary.
        """
        if not messages:
            return current_summary or ""

        # Format conversation for the summarizer
        conversation_text = ""
        for msg in messages:
            role = msg.role.capitalize()
            # Truncate content for safety? 
            content = msg.content or "[Tool Operations]"
            conversation_text += f"{role}: {content}\n"

        prompt_content = (
            "You are an expert summarizer. Condense the following conversation history into a concise summary. "
            "Preserve key facts, decisions, and tool outputs. "
        )
        
        if current_summary:
            prompt_content += f"\n\nExisting Summary:\n{current_summary}\n\nThe following new messages have occurred since the last summary. Update the summary to include them:"
        else:
            prompt_content += "\n\nConversation History:"

        prompt_content += f"\n{conversation_text}\n\nSummary:"

        messages_payload = [
            {"role": "system", "content": "You are a helpful assistant that summarizes conversations."},
            {"role": "user", "content": prompt_content}
        ]

        # Execute
        stream = self.provider.chat_completion(
            messages=messages_payload,
            model=self.model,
            stream=True
        )

        final_summary = ""
        async for event in stream:
            if event and event.get("type") == "content":
                final_summary += event.get("content", "")
        
        return final_summary.strip()

# Global instance
summarizer = ContextSummarizer()
