# Video2Skill — Implementation Plan

Phased implementation per the project milestones. Each milestone delivers real,
testable functionality; nothing moves forward with broken foundations.

## Milestone 1 — Research, repository setup, CLI foundation, Python engine bootstrap, provider abstraction (DONE)

- Repository structure created (packages/cli, packages/core, packages/agent-integrations, engine/*).
- npm package `video2skill` with bin entry; TypeScript CLI compiled to `dist/`.
- Commands implemented: `init`, `learn`, `test`, `evolve`, `list`, `inspect`, `doctor`, `update`, `config`, `help`.
- System probe: Node, Python, FFmpeg, FFprobe, yt-dlp detection.
- Python engine bootstrap: venv creation, pip install of pyyaml/requests.
- Configuration: providers (Anthropic/OpenAI/Google/OpenAI-compatible/local), sandbox, perception, library paths.
- Provider adapters: Anthropic, OpenAI, Google Gemini, OpenAI-compatible, local (real HTTP, no hardcoded keys).
- Provider registry wiring config to provider instances.

Status: Complete. `video2skill init`, `doctor`, `config`, `learn`, `test`, `evolve`, `list`, `inspect` all verified end-to-end.

## Milestone 2 — Video ingestion, FFmpeg, audio extraction, transcription, frame analysis, OCR, timeline alignment

- `engine/perception/video.py`: yt-dlp download, FFmpeg probe, fixed-interval + scene-change keyframe extraction (capped), audio extraction.
- `engine/perception/audio.py`: Whisper transcription (CLI or Python package), graceful fallback when unavailable.
- `engine/perception/ocr.py`: tesseract OCR, graceful fallback.
- `engine/perception/vision.py`: vision event contract.
- `engine/perception/alignment.py`: multimodal timeline (timestamp, transcript, visual, action, UI state, confidence, source reference).
- Adaptive sampling: scene changes add keyframes; total capped to avoid redundant frames.

Status: Implemented with graceful degradation when FFmpeg/yt-dlp/Whisper/tesseract are absent.

## Milestone 3 — Discovery Agent, interview engine, SAS, 95% readiness gate

- `engine/agents/discovery.py`: dynamic, context-aware interview; no repeated questions; follow-ups (e.g. generalize scope); clarification/correction support.
- Skill Acquisition Specification (SAS) data structure.
- Evidence-based readiness score across 8 requirement checks; critical requirements (goal, software, workflow, success criteria) must pass regardless of aggregate.
- 95% gate: blocks acquisition below threshold, lists gaps, permits controlled learning at/above.
- SAS persisted to library.

Status: Complete and verified end-to-end (100% readiness reached in test interview).

## Milestone 4 — Teacher Agent, Research Agent, Skill Architect, skill generation, versioned storage

- `engine/agents/research.py`: findings tagged demonstrated/documented/inference with timestamps and source references.
- `engine/agents/teacher.py`: procedural knowledge (preconditions, tools, actions, expected states, mistakes, recovery, dependencies).
- `engine/agents/architect.py`: SKILL.md rendering + manifest (SKILL.md format: name/description frontmatter, body, evidence).
- `engine/library/store.py`: versioned library, manifest read/save, SAS persistence, SKILL.md read/write, version archiving (never silent overwrite).

Status: Complete. `learn` generates a draft skill package saved to the library.

## Milestone 5 — Isolated same-model and cross-model learners, examination engine, objective scoring

- `engine/learning/learner.py`: fresh learner, skill package + task spec only, sandboxed step execution.
- `engine/evaluation/runner.py`: Examiner Agent, hidden tasks (reproduction, variation, unseen, troubleshooting, recovery, generalization), same-model + cross-model results, combined outcome (Cross-model transferable / Model-specific / Experimental / Failed / Basic verified / Strongly verified).
- Objective verification via sandbox; no LLM self-declaration accepted.

Status: Implemented. Examination gracefully skips when no provider API key is configured (no fake results).

## Milestone 6 — Evolution Agent, regression testing, skill library, agent integrations

- `engine/evolution/engine.py`: collects failure evidence, identifies missing knowledge, archives prior version, bumps version, records changes, status reset to draft (requires re-verification).
- Agent integration files in `integrations/`.

Status: Implemented end-to-end (version archived, bumped to 0.1.1).

## Milestone 7 — Security hardening, npm packaging, installation testing, documentation, release preparation

- Sandbox drivers, refuse-if-unsafe, secrets from env only, no hardcoded keys.
- npm packaging (`files`, `bin`, engines), post-install diagnostics.
- Documentation: README, ARCHITECTURE, RESEARCH, IMPLEMENTATION_PLAN, SECURITY, CONTRIBUTING, TEST_REPORT, EVALUATION_METHODOLOGY, PROVIDER_GUIDE, AGENT_INTEGRATION_GUIDE, SKILL_FORMAT.
- Tests: CLI unit tests, engine import tests, end-to-end flow test.

Status: In progress (documentation and tests being completed in this session).

## Risks

- External media/ML dependencies (FFmpeg, yt-dlp, Whisper) not bundled; installation errors must guide users to install them.
- Model provider API keys required for real learner examinations; without them, examination reports "not configured" rather than fabricating.
- Sandbox availability varies by OS; refuse-fallback is the safe default.
- Copyright / platform restrictions: video download respects yt-dlp support and user-provided access rights; manual upload alternative documented.
