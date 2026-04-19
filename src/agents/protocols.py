from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Signal(str, Enum):
    """Trading signal types."""
    BUY = "BUY"
    STRONG_BUY = "STRONG_BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class AgentOpinion(BaseModel):
    """Represents an individual agent's analysis and recommendation."""
    signal: Signal
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    key_levels: Dict[str, float] = Field(default_factory=dict, description="Key price levels: support, resistance, target")
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw data used for analysis")


class AgentRunStats(BaseModel):
    """Stats for a single agent execution run."""
    tokens_used: int = 0
    tool_calls_count: int = 0
    duration_ms: float = 0.0
    status: str = "success"


class StageResult(BaseModel):
    """Result of an agent stage including stats and opinion."""
    agent_name: str
    stats: AgentRunStats
    opinion: AgentOpinion


class AgentContext(BaseModel):
    """Shared context passed between agents in the multi-agent system."""
    symbol: str
    data: Dict[str, Any] = Field(default_factory=dict, description="Pre-fetched data like quote, history")
    opinions: Dict[str, AgentOpinion] = Field(default_factory=dict, description="Results from previous agents (agent_name -> AgentOpinion)")
    risk_flags: List[str] = Field(default_factory=list, description="List of identified risk flags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
