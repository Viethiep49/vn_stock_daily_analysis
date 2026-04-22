from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import date, datetime

from src.core.llm_client import LiteLLMClient
from src.agents.protocols import AgentContext, AgentOpinion, Signal
from src.agents.tools.registry import default_registry
from src.agents.runner import AgentRunner
from src.utils.json_helper import parse_json_robustly

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.
    Handles the LLM -> Tool -> LLM loop using AgentRunner.
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
        system_prompt = self.system_prompt(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.user_prompt(context)}
        ]

        runner = AgentRunner(llm_client=self.llm_client)
        final_text, stats = runner.run(system_prompt, messages, self.registry)
        
        opinion = self._parse_opinion(final_text)

        # Log telemetry
        try:
            from src.utils.telemetry import log_stage_result
            from src.agents.protocols import StageResult
            stage_result = StageResult(
                agent_name=self.__class__.__name__,
                stats=stats,
                opinion=opinion
            )
            log_stage_result(stage_result)
        except Exception as e:
            logger.error(f"Failed to log telemetry for {self.__class__.__name__}: {e}")
            
        return opinion

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
            data = parse_json_robustly(content)
            if "signal" in data:
                if isinstance(data["signal"], str):
                    try:
                        data["signal"] = Signal(data["signal"].upper())
                    except ValueError:
                        data["signal"] = Signal.HOLD
                        
            # Robust confidence parsing
            if "confidence" in data:
                conf = data["confidence"]
                if isinstance(conf, str):
                    conf = conf.lower().strip()
                    if conf in ["high", "strong"]:
                        data["confidence"] = 0.8
                    elif conf in ["medium", "moderate"]:
                        data["confidence"] = 0.5
                    elif conf in ["low", "weak"]:
                        data["confidence"] = 0.2
                    else:
                        try:
                            data["confidence"] = float(conf)
                        except ValueError:
                            data["confidence"] = 0.5
            
            return AgentOpinion(**data)
        except Exception as e:
            logger.warning(f"Failed to parse AgentOpinion from content: {e}")
            
        return AgentOpinion(
            signal=Signal.HOLD,
            confidence=0.5,
            reasoning=content
        )