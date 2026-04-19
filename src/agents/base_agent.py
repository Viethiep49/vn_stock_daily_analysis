from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import logging
import re

from src.core.llm_client import LiteLLMClient
from src.agents.protocols import AgentContext, AgentOpinion, Signal
from src.agents.tools.registry import default_registry

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.
    Handles the LLM -> Tool -> LLM loop.
    """
    
    def __init__(self, llm_client: Optional[LiteLLMClient] = None, registry=None):
        self.llm_client = llm_client or LiteLLMClient()
        self.registry = registry or default_registry

    @abstractmethod
    def system_prompt(self, context: AgentContext) -> str:
        """Define the agent's system prompt based on context."""
        pass

    @abstractmethod
    def user_prompt(self, context: AgentContext) -> str:
        """Define the agent's user prompt based on context."""
        pass

    def run(self, context: AgentContext) -> AgentOpinion:
        """
        Execute the agent loop: LLM -> Tool -> LLM -> Opinion.
        """
        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": self.user_prompt(context)}
        ]

        tools = self.registry.get_schemas()
        
        # Max iterations to avoid infinite loops
        max_iterations = 10
        for i in range(max_iterations):
            try:
                response = self.llm_client.chat(messages=messages, tools=tools)
                
                # Handle unexpected response format (e.g. from mock)
                if not hasattr(response, 'choices') or not response.choices:
                    content = str(response)
                    return self._parse_opinion(content)
                
                message = response.choices[0].message
                messages.append(message)

                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            tool_args = {}
                        
                        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                        try:
                            result = self.registry.execute(tool_name, **tool_args)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": json.dumps(result)
                            })
                        except Exception as e:
                            logger.error(f"Error executing tool {tool_name}: {e}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": json.dumps({"error": str(e)})
                            })
                    continue # Ask LLM again with tool results
                
                # No more tool calls, parse final answer
                return self._parse_opinion(message.content)
            
            except Exception as e:
                logger.error(f"LLM loop error: {e}")
                return AgentOpinion(
                    signal=Signal.HOLD,
                    confidence=0.0,
                    reasoning=f"Error in agent loop: {str(e)}"
                )

        return AgentOpinion(
            signal=Signal.HOLD,
            confidence=0.0,
            reasoning="Agent reached max iterations without a final answer."
        )

    def _parse_opinion(self, content: str) -> AgentOpinion:
        """
        Parse LLM string content into AgentOpinion object.
        Expects a JSON block in the response.
        """
        if not content:
            return AgentOpinion(
                signal=Signal.HOLD,
                confidence=0.0,
                reasoning="Empty response from LLM"
            )

        try:
            # Try to find JSON block
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                # Basic validation/defaulting for AgentOpinion
                if "signal" in data:
                    # Convert string to Signal enum if needed
                    if isinstance(data["signal"], str):
                        try:
                            data["signal"] = Signal(data["signal"].upper())
                        except ValueError:
                            data["signal"] = Signal.HOLD
                return AgentOpinion(**data)
        except Exception as e:
            logger.warning(f"Failed to parse AgentOpinion from content: {e}")
            
        return AgentOpinion(
            signal=Signal.HOLD,
            confidence=0.5,
            reasoning=content
        )
