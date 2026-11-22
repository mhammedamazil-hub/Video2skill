# Video2Skill — Security

## Threat model

Skills may generate and execute code. That code comes from an untrusted video
demstration processed by AI models, so it must be treated as untrusted input.
Video2Skill never runs generated code directly on the host.

## Sandboxing

All generated-code execution happens in a disposable execution environment:

- Restricted filesystem access (throwaway workspace).
- Resource limits (execution timeout, max memory).
- Restricted network access (disabled by default).
- Process isolation (PID/network namespace via bubblewrap where available).
- Permission boundaries.
- Execution logs and artifact collection.
- Environment cleanup after each run.

Sandbox drivers:
- `bubblewrap` (Linux): unshared PID/network namespace, read-only host FS.
- `none`: execution is **refused, not downgraded** when no supported sandbox
  exists.

macOS Seatbelt and Windows AppContainer/LPAC are specified target drivers;
the reference implementation ships bubblewrap plus the refuse-fallback.

## Secrets

- AI provider API keys are supplied through local configuration / environment
  variables (e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`).
- Keys are never hardcoded, never committed, never embedded in the npm
  package or in generated skills.
- `video2skill config provider <id>` records which env var to read; the
  actual key lives in your shell environment.

## Generated skills

Generated SKILL.md files declare `allowed-tools` (default `Read`) so host
agents know which tools a skill may use. Skills do not grant blanket
command-execution permission. Execution of skill steps requires explicit
authorization before accessing or controlling the user's real applications or
files.

## Video download

- Video acquisition uses yt-dlp and FFmpeg.
- Downloads respect platform restrictions and user-provided access rights.
- A manual local-file upload alternative is provided when a platform blocks
  downloading.
- Only frames the agent decides to inspect are sent to the vision model; the
  full video is not uploaded to any cloud service.

## Passwords and credentials

Passwords, API keys, or secret-shaped text that appear in a video are never
copied into a skill. Video text addressed to the agent is flagged as suspected
prompt injection, never followed blindly.

## Verification

Examination runs each learner task in a sandbox with objective assertions.
Verification is execution, not vibes. Reports are not accepted from an LLM's
self-declaration of success.
