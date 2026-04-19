import time
import json
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.llm_client import LiteLLMClient
from src.agents.tools.registry import default_registry

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle date/datetime objects."""
    def default(self, obj):
        from datetime import date, datetime
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

class AgentRunner:
    def __init__(self, llm_client: Optional[LiteLLMClient] = None, max_iterations: int = 10, timeout_seconds: int = 45):
        self.llm_client = llm_client or LiteLLMClient()
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds

    def run(self, system_prompt: str, messages: List[Dict[str, Any]], registry: Any = None) -> str:
        registry = registry or default_registry
        tools = registry.get_schemas()
        called_tools = set()
        start_time = time.time()
        last_valid_text = ""

        for i in range(self.max_iterations):
            if time.time() - start_time > self.timeout_seconds:
                logger.warning("AgentRunner: Budget exceeded (45s). Breaking loop.")
                return last_valid_text or '{"error": "timeout"}'

            try:
                response = self.llm_client.chat(messages=messages, tools=tools)
                
                # Handle unexpected response format
                if not hasattr(response, 'choices') or not response.choices:
                    return str(response)
                
                message = response.choices[0].message
                messages.append(message)

                if getattr(message, 'content', None):
                    last_valid_text = str(message.content)
                
                if getattr(message, 'tool_calls', None):
                    tool_calls = message.tool_calls
                    tool_messages = []
                    futures = []
                    
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        for tc in tool_calls:
                            tool_name = tc.function.name
                            try:
                                tool_args = json.loads(tc.function.arguments)
                            except json.JSONDecodeError:
                                tool_args = {}
                                
                            args_str = json.dumps(tool_args, sort_keys=True)
                            cache_key = f"{tool_name}:{args_str}"
                            
                            if cache_key in called_tools:
                                logger.info(f"Tool {tool_name} already called with args {args_str}, skipping.")
                                tool_messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "name": tool_name,
                                    "content": json.dumps({"error": "Tool already called, skipping"})
                                })
                                continue
                                
                            called_tools.add(cache_key)
                            
                            def exec_tool(name, args, call_id):
                                logger.info(f"Executing tool: {name} with args: {args}")
                                try:
                                    res = registry.execute(name, **args)
                                    return {
                                        "role": "tool",
                                        "tool_call_id": call_id,
                                        "name": name,
                                        "content": json.dumps(res, cls=DateTimeEncoder)
                                    }
                                except Exception as e:
                                    logger.error(f"Error executing tool {name}: {e}")
                                    return {
                                        "role": "tool",
                                        "tool_call_id": call_id,
                                        "name": name,
                                        "content": json.dumps({"error": str(e)})
                                    }
                                    
                            futures.append(executor.submit(exec_tool, tool_name, tool_args, tc.id))
                            
                        for future in as_completed(futures):
                            tool_messages.append(future.result())
                    
                    # Sort results back to original tool_calls order
                    results_by_id = {tm["tool_call_id"]: tm for tm in tool_messages}
                    for tc in tool_calls:
                        if tc.id in results_by_id:
                            messages.append(results_by_id[tc.id])
                            
                    continue # Ask LLM again with tool results
                
                # No more tool calls, return final answer
                return str(message.content) if message.content else ""
            
            except Exception as e:
                logger.error(f"LLM loop error: {e}")
                return last_valid_text or str(e)
                
        logger.warning("AgentRunner: Max iterations reached.")
        return last_valid_text or '{"error": "max_iterations_reached"}'