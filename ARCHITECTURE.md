# Video2Skill Architecture

## Overview

Video2Skill is a TypeScript npm CLI plus a Python processing engine. The CLI
handles installation, configuration, command routing, and diagnostics. The
Python engine runs the seven agents, perception pipeline, model providers,
skill library, sandboxing, and examination.

## Project structure

```
video2skill/
├── package.json                 # publishable npm package (bin: video2skill)
├── packages/cli/src/            # TypeScript CLI source
│   ├── index.ts                 # command router
│   ├── config.ts                # configuration (providers, sandbox, library)
│   ├── engine.ts                # system probe + Python engine bootstrap
│   └── commands/                # init, learn, test, evolve, list, inspect, update, config
├── engine/                      # Python processing engine
│   ├── bootstrap.py             # CLI entry point (discover/examine/evolve)
│   ├── config.py                # engine configuration
│   ├── agents/
│   │   ├── base.py              # Agent base class + structured I/O
│   │   ├── discovery.py         # Discovery Agent + interview + readiness gate
│   │   ├── research.py          # Research Agent
│   │   ├── teacher.py           # Teacher Agent
│   │   ├── architect.py         # Skill Architect
│   │   └── (learner/examiner/evolution in learning/, evaluation/, evolution/)
│   ├── perception/
│   │   ├── video.py             # yt-dlp download, FFmpeg probe/frame/audio extract
│   │   ├── audio.py             # Whisper transcription
│   │   ├── vision.py            # vision-model event contract
│   │   ├── ocr.py               # OCR (tesseract)
│   │   └── alignment.py         # multimodal timeline
│   ├── providers/
│   │   ├── base.py              # Provider base adapter
│   │   ├── anthropic.py         # Anthropic adapter
│   │   ├── openai.py            # OpenAI adapter
│   │   ├── google.py            # Google Gemini adapter
│   │   ├── openai_compatible.py # OpenAI-compatible adapter
│   │   ├── local.py             # Local inference server adapter
│   │   └── registry.py          # provider factory
│   ├── learning/
│   │   └── learner.py           # isolated Learner Agent
│   ├── evaluation/
│   │   └── runner.py            # Examiner Agent + examination runner
│   ├── evolution/
│   │   └── engine.py            # Evolution Agent
│   ├── library/
│   │   └── store.py             # versioned skill library
│   └── sandbox/
│       └── base.py              # disposable sandboxed execution
├── templates/                   # skill templates
├── integrations/                # agent integration files
├── docs/
├── scripts/
├── examples/
└── dist/                        # compiled CLI output
```

## Agents

Each agent is independent: separate responsibilities, context, permissions,
state, tools, and structured input/output contracts. No agent inherits another
agent's conversation history, private notes, or hidden answers.

### Agent 1 — Discovery

Interviews the user before skill acquisition. Asks dynamic, context-aware
follow-up questions based on previous answers, never repeats a question, and
produces a structured Skill Acquisition Specification (SAS). Computes an
evidence-based readiness score (not an LLM self-declaration) and enforces the
95% gate.

### Agent 2 — Research

Acquires knowledge from video, audio, documentation, and related resources.
Every finding is tagged with its evidence type:

- `demonstrated` — observed in the video (timestamped)
- `documented` — from official docs / manuals
- `inference` — AI-derived, not directly evidenced

### Agent 3 — Teacher

Converts demonstrations into procedural knowledge: preconditions, required
tools, initial state, actions, action sequences, decision points, parameters,
expected intermediate states, final results, common mistakes, error recovery,
alternative approaches, and dependencies between actions.

### Agent 4 — Skill Architect

Generates the portable skill package: SKILL.md, detailed instructions, scripts,
references, examples, dependencies, procedures, error recovery, verification
tests, evidence references, and version metadata.

### Agent 5 — Learner

Creates genuinely fresh learner instances. Receives only the foundation model's
normal capabilities, the generated skill package, explicitly permitted tools,
approved resources, and the task specification. No teacher history, no private
notes, no hidden answers.

### Agent 6 — Examiner

Independently generates hidden tasks unknown to the learners and objectively
verifies results (real files, application states, automated assertions,
execution results). Never accepts an LLM's self-declaration of success.

### Agent 7 — Evolution

Improves existing skills from failure evidence: collects failures, identifies
missing knowledge, archives the prior version, revises the skill, and records
the change. Never silently overwrites a verified skill.

## Readiness gate

The system does not begin final skill acquisition until readiness >= 95%.
Readiness is evidence-based across: requirement completeness, source coverage,
audio/visual understanding, procedural completeness, software compatibility,
dependency identification, technical feasibility, execution environment,
test-plan completeness, evidence quality, and unresolved contradictions.
Critical requirements (goal, software, workflow, success criteria) must be
satisfied regardless of the aggregate score.

## Dual-model learning

Two independent examinations under equivalent conditions:

- **Learner A (same-model transfer)** — same foundation model as the Teacher,
  fresh isolated instance.
- **Learner B (cross-model transfer)** — a different foundation model, same
  skill package and equivalent resources.

Evaluation outcomes: Experimental, Failed, Basic verified, Strongly verified,
Model-specific, Cross-model transferable. A skill is never universally verified
based on one successful task.

## Sandboxing

Generated code executes in disposable, restricted environments with restricted
filesystem access, resource limits, execution timeouts, restricted network
access, process isolation, permission boundaries, execution logs, artifact
collection, and environment cleanup. Where no supported sandbox exists,
execution is refused, not downgraded.

## Skill library

Persistent local library with unique IDs, versioning, search, import, export,
update, duplicate detection, version comparison, rollback, skill dependencies,
and composition. A verified skill never loses verification silently after
modification; changed versions undergo regression testing.

## Model providers

API keys are supplied through local configuration/environment variables and are
never hardcoded. Supported: Anthropic, OpenAI, Google Gemini, OpenAI-compatible,
local inference servers.
