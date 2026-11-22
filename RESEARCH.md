# Video2Skill — Research

Record of repositories, papers, architectural findings, limitations, and
decisions that informed the Video2Skill design.

## Agent skills ecosystem

### skills.sh (Vercel Labs)

- https://skills.sh/
- CLI: https://github.com/vercel-labs/skills (MIT)
- Open directory for AI agent skills. Skills are installed with
  `npx skills add <owner/repo>` and work across 20+ agents (Claude Code,
  Cursor, Codex, GitHub Copilot, Windsurf, Gemini CLI, Cline, Zed, …).
- Skill format: SKILL.md — a folder with a SKILL.md file containing YAML
  frontmatter (required: `name`, `description`) plus a Markdown body, with
  optional bundled references/, scripts/, assets/ loaded via progressive
  disclosure.
- Verification: skills are inspected before install; security audit results
  shown on the directory.

Finding: SKILL.md is the de facto portable skill format. Video2Skill emits
skills in this format so they install into any supported agent environment.

### Verified skills considered for installation

The spec directs researching `npx skills add <verified-repository>` for
autonomous agent development, orchestration, skill authoring, Claude Code /
Codex integration, TypeScript/Python architecture, video processing, FFmpeg,
multimodal AI, computer-use agents, browser automation, agent evaluation,
benchmark design, testing/debugging, security/sandboxing, npm development, and
documentation.

Decision: Video2Skill does not blindly install random skill repositories. The
CLI focuses on generating its own skills from video demonstrations. Where a
relevant, maintained, official skill exists (e.g. via skills.sh), users may
install it separately with `npx skills add <owner/repo>`. Video2Skill's agent
integration guide documents how to add Video2Skill-generated skills to agent
environments.

## Prior art: video-to-skill

- https://github.com/brenoepics/video-to-skill (MIT)
- Turns tutorial videos into verified, installable agent skills; reads pixels
  not just transcript; word-timestamped Whisper; pHash shot detection; motion
  density; fresh sandboxed sub-agent verification; OS sandboxing
  (Windows LPAC/AppContainer, macOS Seatbelt, Linux bubblewrap); installs to
  `~/.agents/skills`; version-pinned, SHA-256-verified downloads.

Architectural influence: deterministic local extraction → agent reads keyframes
selectively → evidence-grounded steps with `[t=MM:SS]` provenance → sandboxed
verification → install. Video2Skill adopts these principles but implements an
original TypeScript CLI + Python engine architecture rather than cloning the
Rust-based extractor.

## Research papers

### RESOURCE2SKILL: Distilling Executable Agent Skills from Human-Created Multimodal Resources
- https://www.alphaxiv.org/abs/2606.29538
- Distills executable skills from tutorial videos, repositories, articles, and
  artifacts into a hierarchical multimodal Skill Wiki. Construction operator
  f_theta maps resources to candidate skills; acceptance predicate A_D filters.
- Influence: multimodal distillation pipeline, provenance, skill wiki /
  library organization, online acquisition when coverage is insufficient.

### Video-as-Experience (VEX): Learning Computer Use via Audio-Visual Understanding
- https://arxiv.org/abs/2611.18747
- Audio-visual understanding of tutorial videos for unified procedural learning
  and self-verification in computer-use agents.
- Influence: audio-visual alignment, self-verification of learned procedures.

### Related areas investigated

- Computer-use agents / GUI agents (imitation learning from video).
- Multimodal video understanding, action recognition, OCR of UI/code.
- Agent evaluation, benchmark design, hidden task generation.
- Agent memory, skill libraries, skill evolution, regression testing.
- Voyager (skill library from own traces) — contrasted with RESOURCE2SKILL,
  which distills from external human resources.

## Architectural decisions

| Decision | Rationale |
|---|---|
| TypeScript CLI + Python engine | Matches spec; keeps npm package lightweight, offloads heavy media/ML to Python |
| SKILL.md output format | Portable across Claude Code, Codex, Cursor, Gemini CLI |
| yt-dlp + FFmpeg for ingestion | Industry-standard, platform-supported downloading and media processing |
| Whisper-compatible transcription | Timestamped, language-detecting speech recognition |
| Dual-model (same + cross-model) learners | Required by spec; prevents model-specific overfitting |
| Sandbox-first execution, refuse-if-unsafe | Security requirement; never run generated code unconfined |
| Versioned library with archiving | Prevents silent overwrites of verified skills |
| Evidence-based readiness (not LLM self-declared) | Required by the 95% gate |

## Limitations (known)

- FFmpeg, yt-dlp, Whisper, tesseract, and bubblewrap are external
  dependencies; the CLI bootstraps a minimal Python venv but does not bundle
  heavy media/ML binaries.
- Video perception (frame extraction, scene detection, OCR, vision) is
  wired but requires FFmpeg/yt-dlp/Whisper to be present to produce real
  evidence. Without them, discovery still proceeds from the user interview.
- Model provider adapters make real HTTP calls; they gracefully report
  "not configured" when no API key is present — they do not fabricate results.
- Sandboxing uses bubblewrap on Linux when available; otherwise execution is
  refused. macOS Seatbelt / Windows AppContainer drivers are specified but the
  reference implementation ships with bubblewrap + refuse-fallback.
- No mandatory cloud backend or subscription; all processing is local.

## Compatibility

Supported: Windows, Linux, macOS. Node.js >= 18, Python 3.9+.
