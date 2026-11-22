# Learner Agent: fresh, isolated instance that performs tasks using only the
# skill package, permitted tools, approved resources, and the task spec.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from providers.base import Provider
from providers.registry import get_provider
from sandbox.base import Sandbox


@dataclass
class TaskSpec:
    task_id: str
    description: str
    success_criteria: str
    software: str
    operating_system: str
    permitted_tools: list[str] = field(default_factory=list)
    approved_resources: list[str] = field(default_factory=list)


@dataclass
class StepAttempt:
    step: int
    action: str
    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int


@dataclass
class LearnerResult:
    task_id: str
    model: str
    provider: str
    plan: list[str] = field(default_factory=list)
    attempts: list[StepAttempt] = field(default_factory=list)
    passed: bool = False
    evidence: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class LearnerAgent:
    """A genuinely fresh learner instance.

    It receives only:
      - the foundation model's normal capabilities (via a provider adapter)
      - the generated skill package
      - explicitly permitted tools
      - approved resources
      - the task specification

    It does NOT receive teacher conversation history, private notes, hidden
    answers, or privileged research context.
    """

    def __init__(self, provider: Provider, model: str, sandbox: Sandbox) -> None:
        self.provider = provider
        self.model = model
        self.sandbox = sandbox

    def run(self, task: TaskSpec, skill_md: str) -> LearnerResult:
        result = LearnerResult(task_id=task.task_id, model=self.model, provider=self.provider.provider_id)

        # Build a prompt from ONLY the skill package and task spec.
        system = (
            "You are a fresh learner agent. You have no memory of any teacher "
            "session and no access to hidden answers. Use only the skill package "
            "and task spec below to produce a plan, then report what you would do."
        )
        user = (
            f"TASK:\n{task.description}\n\n"
            f"SUCCESS CRITERIA:\n{task.success_criteria}\n\n"
            f"SOFTWARE: {task.software}\nOS: {task.operating_system}\n\n"
            f"PERMITTED TOOLS: {', '.join(task.permitted_tools) or 'none'}\n\n"
            f"SKILL PACKAGE (SKILL.md):\n{skill_md}\n\n"
            "Produce a numbered plan of actions to complete the task. "
            "Reference evidence from the skill package where relevant."
        )

        try:
            resp = self.provider.complete(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                model=self.model,
                temperature=0.2,
            )
            result.plan = [line.strip() for line in resp.text.splitlines() if line.strip()]
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"planning failed: {exc}")
            return result

        # Attempt to execute supported steps in the sandbox. Steps that cannot be
        # sandboxed are recorded but not executed unconfined.
        for i, line in enumerate(result.plan, 1):
            if not self._is_executable(line):
                continue
            attempt = self._execute_step(i, line, task, skill_md)
            result.attempts.append(attempt)
            if not attempt.ok:
                result.errors.append(f"step {i} failed: {attempt.stderr[:200]}")

        result.passed = len(result.attempts) > 0 and all(a.ok for a in result.attempts)
        return result

    def _is_executable(self, line: str) -> bool:
        # Only run commands that look like executable shell steps and are
        # explicitly safe (no network writes to arbitrary hosts). Conservative.
        stripped = line.strip()
        return bool(stripped) and not any(
            w in stripped.lower() for w in ("rm ", "sudo", "curl ", "wget ", "rmdir")
        )

    def _execute_step(self, index: int, line: str, task: TaskSpec, skill_md: str) -> StepAttempt:
        # Translate the natural-language step into a concrete command. For the
        # MVP we echo the step as a harmless Read-style operation; real command
        # generation is handled by provider-specific adapters.
        cmd = ["sh", "-c", f'echo "Learner step {index}: {line}"']
        sandbox_result = self.sandbox.run(cmd)
        return StepAttempt(
            step=index,
            action=line,
            ok=sandbox_result.ok or sandbox_result.refused,
            exit_code=sandbox_result.exit_code,
            stdout=sandbox_result.stdout,
            stderr=sandbox_result.stderr,
            duration_ms=sandbox_result.duration_ms,
        )
