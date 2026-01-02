import openai
from typing import AsyncGenerator, Dict, List, Any
from app.core.config import settings
from app.services.llm.base import BaseLLM
from app.services.tools_bridge import tools_bridge
import json
import tiktoken
import time
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class OpenAIProvider(BaseLLM):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        
        # Azure OpenAI support
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            self.client = openai.AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version="2024-02-15-preview",
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME
            )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        stream: bool = False,
        tools: List[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        # Base parameters
        completion_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True, # We force stream for the agent loop
            "stream_options": {"include_usage": True},
        }
        
        if tools:
            completion_params["tools"] = tools
            completion_params["tool_choice"] = "auto"

        # 1. Start the Stream
        with tracer.start_as_current_span("openai_completion_create") as span:
            span.set_attribute("llm.model", model)
            response = await self.client.chat.completions.create(**completion_params)
        
        # State capability for tool accumulation
        tool_calls_buffer = [] 
        
        async for chunk in response:
            # Usage tracking (last chunk)
            if hasattr(chunk, 'usage') and chunk.usage:
                yield {"type": "usage", "usage": chunk.usage.model_dump()}

            if not chunk.choices:
                continue
                
            choice = chunk.choices[0]
            delta = choice.delta

            # A. Text Content: Yield immediately
            if delta.content:
                yield {"type": "content", "content": delta.content}

            # B. Tool Calls: Accumulate chunks
            if delta.tool_calls:
                for tc_chunk in delta.tool_calls:
                    if len(tool_calls_buffer) <= tc_chunk.index:
                        tool_calls_buffer.append({
                            "id": tc_chunk.id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        })
                    
                    tc = tool_calls_buffer[tc_chunk.index]
                    if tc_chunk.id: tc["id"] = tc_chunk.id
                    if tc_chunk.function.name: tc["function"]["name"] += tc_chunk.function.name
                    if tc_chunk.function.arguments: tc["function"]["arguments"] += tc_chunk.function.arguments
        
        # 2. Check if we have gathered tool calls to execute
        if tool_calls_buffer:
            # Yield a thought marker
            yield {"type": "thought", "content": "Using tools..."}
            
            # Append the assistant's decision to call tools to history
            assistant_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls_buffer
            }
            messages.append(assistant_msg)
            # Yield persist event for the assistant message (tool calls)
            yield {"type": "persist", "msg": assistant_msg}

            # 3. Execute Tools
            for tool_call in tool_calls_buffer:
                func_name = tool_call["function"]["name"]
                args_str = tool_call["function"]["arguments"]
                call_id = tool_call["id"]
                
                try:
                    arguments = json.loads(args_str)
                    # Yield structured info about the call
                    yield {"type": "thought", "content": f"Calling `{func_name}`..."}
                    
                    start_time = time.time() # Optional: track tool execution time
                    
                    with tracer.start_as_current_span("tool_execution", attributes={"tool.name": func_name}) as span:
                        try:
                            result = await tools_bridge.execute_tool(func_name, arguments)
                        except Exception as e:
                            span.record_exception(e)
                            result = {"error": str(e)}

                    # Determine status
                    status = "error" if isinstance(result, dict) and "error" in result else "success"
                    # Add status to span if context is available? (Span closed)
                    
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"], # Use tool_call["id"] instead of tool_call.id
                        "content": json.dumps(result),
                        "status": status
                    }

                    # 4.3 Yield Tool Output (Persist)
                    yield {"type": "persist", "msg": tool_msg}
                    
                    # Also yield thought about completion
                    if status == "error":
                        yield {"type": "thought", "content": f"Error in `{func_name}`: {result.get('error')}"}
                    else:
                        yield {"type": "thought", "content": f"`{func_name}` output received."}
                    
                    messages.append(tool_msg)
                except json.JSONDecodeError as e:
                    # Handle JSON parsing error for tool arguments
                    error_msg = f"Error parsing arguments for tool '{func_name}': {e}"
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps({"error": error_msg}),
                        "status": "error"
                    }
                    messages.append(tool_msg)
                    yield {"type": "persist", "msg": tool_msg}
                    yield {"type": "thought", "content": error_msg}
                except Exception as e:
                    # Catch any other unexpected errors during tool preparation/execution
                    error_msg = f"An unexpected error occurred during tool '{func_name}' execution: {e}"
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps({"error": error_msg}),
                        "status": "error"
                    }
                    messages.append(tool_msg)
                    yield {"type": "persist", "msg": tool_msg}
                    yield {"type": "thought", "content": error_msg}

            # 4. Recursively Call LLM with new history (Propagate stream)
            async for chunk in self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                stream=True,
                tools=tools
            ):
                yield chunk

    def count_tokens(self, text: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
