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
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sentiment_score: int = Field(default=50, ge=0, le=100)
    operation_advice: str = Field(default="")
    key_points: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="")
    # Use Any to bypass strict validation of nested levels (like lists vs floats)
    key_levels: Any = Field(default_factory=dict)
    raw_data: Optional[Dict[str, Any]] = Field(default=None)


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
    data: Dict[str, Any] = Field(default_factory=dict)
    opinions: Dict[str, AgentOpinion] = Field(default_factory=dict)
    risk_flags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
