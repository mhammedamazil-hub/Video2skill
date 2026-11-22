# Video2Skill

Autonomous Multimodal Skill Acquisition, Learning, Testing & Evolution Engine

Video2Skill teaches AI agents **how to do things**, not just what things are.
Give it a tutorial video, answer a dynamic discovery interview, reach a 95%
evidence-based readiness gate, and it generates a portable, verified agent
skill — then examines it with isolated same-model and cross-model learners.

```
npx video2skill
npx video2skill init
npx video2skill learn "VIDEO_URL"
npx video2skill test skill-name
npx video2skill evolve skill-name
npx video2skill list
npx video2skill inspect skill-name
npx video2skill doctor
npx video2skill update
```

## What it is NOT

- Not a video summarizer.
- Not a simple YouTube-to-SKILL.md converter.
- No fake agents, no simulated learning, no placeholder verification.

## Core architecture

Seven independent agents, each with separate responsibilities, context,
permissions, state, tools, and structured input/output contracts:

1. **Discovery Agent** — interviews the user, produces a Skill Acquisition
   Specification, and enforces the 95% readiness gate.
2. **Research Agent** — acquires knowledge and tags every finding as
   demonstrated / documented / inference with traceable evidence.
3. **Teacher Agent** — converts demonstrations into procedural knowledge
   (preconditions, actions, decision points, error recovery, …).
4. **Skill Architect** — builds the portable skill package (SKILL.md + manifest).
5. **Learner Agent** — fresh, isolated instance that performs tasks using only
   the skill package and permitted tools.
6. **Examiner Agent** — generates hidden tasks and objectively verifies results.
7. **Evolution Agent** — improves failed skills, archives prior versions.

## Dual-model learning

Two independent examinations:
- **Learner A** — same foundation model as the Teacher (same-model transfer).
- **Learner B** — a different foundation model (cross-model transfer).

Provider adapters: Anthropic, OpenAI, Google Gemini, OpenAI-compatible, and
local inference servers. API keys come from local configuration — never
hardcoded.

## Sandboxing

Generated code executes in disposable, restricted environments (bubblewrap on
Linux where available). Where no supported sandbox exists, execution is
**refused, not downgraded**.

## Skill distribution

Skills use the open SKILL.md format (Anthropic's Agent Skills standard) and are
installable into Claude Code, OpenAI Codex, Cursor, Gemini CLI, and other
compatible agent environments.

## Documentation

| Document | Purpose |
|---|---|
| ARCHITECTURE.md | System design, agent contracts, project structure |
| RESEARCH.md | Ecosystem research, papers, decisions and limitations |
| IMPLEMENTATION_PLAN.md | Phased implementation plan and milestones |
| SECURITY.md | Sandboxing, secrets, generated-code execution |
| SKILL_FORMAT.md | Skill package format and versioning |
| PROVIDER_GUIDE.md | Configuring AI model providers |
| AGENT_INTEGRATION_GUIDE.md | Claude Code, Codex, Cursor, Gemini CLI |
| EVALUATION_METHODOLOGY.md | Learner examination and scoring |
| TEST_REPORT.md | Test results and known limitations |
| CONTRIBUTING.md | How to contribute |

## Quick start

```bash
# 1. Install (from npm once published)
npm install -g video2skill   # or: npx video2skill

# 2. Initialize the local engine
video2skill init

# 3. Configure an AI provider
video2skill config provider anthropic --set-default
export ANTHROPIC_API_KEY=sk-...

# 4. Verify the environment
video2skill doctor

# 5. Acquire a skill from a tutorial video
video2skill learn "https://youtube.com/watch?v=..."

# 6. Examine it with isolated learners
video2skill test <skill-name>

# 7. Improve a failed skill
video2skill evolve <skill-name>
```

## Requirements

- Node.js >= 18
- Python 3.9+
- FFmpeg + yt-dlp (for video ingestion; optional for the CLI to run)
- An AI provider API key (Anthropic/OpenAI/Google/local)

## License

MIT
