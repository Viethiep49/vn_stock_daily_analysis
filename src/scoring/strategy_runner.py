"""YAML-driven strategy definition + safe rule evaluation."""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from src.scoring.signals import Signal


class RuleConfig(BaseModel):
    when: Optional[str] = None
    default: bool = False
    score: int = Field(ge=0, le=100)
    signal: Signal
    reason: str

    @model_validator(mode="after")
    def _xor_when_default(self):
        if self.default and self.when:
            raise ValueError("Rule cannot have both `default` and `when`")
        if not self.default and not self.when:
            raise ValueError("Rule must have either `when` or `default: true`")
        return self


class StrategyConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    weight: float = Field(gt=0)
    enabled: bool = True
    indicators_required: List[str] = Field(default_factory=list)
    rules: List[RuleConfig] = Field(min_length=1)

    @field_validator("rules")
    @classmethod
    def _validate_rules(cls, rules: List[RuleConfig]) -> List[RuleConfig]:
        defaults = [i for i, r in enumerate(rules) if r.default]
        if len(defaults) != 1:
            raise ValueError(
                f"Exactly one rule must have `default: true`, got {len(defaults)}"
            )
        if defaults[0] != len(rules) - 1:
            raise ValueError("Default rule must be the LAST rule")
        return rules
