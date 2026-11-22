"""Base class for Video2Skill agents.

Every agent exposes a structured input/output contract:
  - input:  a dataclass / dict describing what the agent receives
  - output: a dataclass / dict describing what the agent produces
Agents are independent: they share no conversation history, no private notes,
and no hidden context unless explicitly passed through the input contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentInput:
    """Structured input to an agent."""

    context: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Structured output from an agent."""

    ok: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "evidence": self.evidence,
            "warnings": self.warnings,
            "errors": self.errors,
        }


class Agent:
    """Base agent. Subclasses implement `run`."""

    name: str = "agent"

    def run(self, input: AgentInput) -> AgentOutput:  # noqa: A002 - shadowing builtin is intentional here
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
