# Video2Skill — Provider Guide

Video2Skill supports multiple foundation-model providers through adapters.
API keys are supplied through local configuration/environment variables and are
never hardcoded.

## Configure a provider

```bash
video2skill init
video2skill config provider anthropic --default-model claude-3-5-sonnet-20241022 --set-default
```

Then set the API key in your shell:

```bash
export ANTHROPIC_API_KEY=sk-...
```

## Supported providers

| Provider | ID | Env var | Default model | Notes |
|---|---|---|---|---|
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | claude-3-5-sonnet-20241022 | https://api.anthropic.com |
| OpenAI | `openai` | `OPENAI_API_KEY` | gpt-4o | https://api.openai.com |
| Google Gemini | `google` | `GEMINI_API_KEY` | gemini-1.5-pro | generativelanguage.googleapis.com |
| OpenAI-compatible | `openai-compatible` | `OPENAI_COMPATIBLE_API_KEY` + `OPENAI_COMPATIBLE_BASE_URL` | local-model | any OpenAI-chat-schema endpoint |
| Local inference server | `local` | `LOCAL_MODEL_BASE_URL` (+ `LOCAL_MODEL`) | llama3.1 | Ollama / llama.cpp / TGI fallback |

## Provider configuration fields

- `type` — one of: anthropic, openai, google, openai-compatible, local.
- `apiKeyEnv` — environment variable holding the API key (empty for local).
- `baseUrl` — custom base URL (openai-compatible / local).
- `defaultModel` — default model identifier.
- `enabled` — whether the provider is eligible for use.

## Dual-model learning

Two independent examinations run under equivalent conditions:

- **Learner A (same-model transfer)** — same foundation model as the Teacher,
  fresh isolated instance.
- **Learner B (cross-model transfer)** — a different configured provider/model,
  same skill package and equivalent resources.

A skill is "Cross-model transferable" only if both learners pass. It is
"Model-specific" if only the Teacher's model passes. Configure at least two
providers to test cross-model transfer meaningfully.

## Viewing configuration

```bash
video2skill config show
```

Never commit API keys. Add `.video2skill/` to your `.gitignore` if it ever
contains real keys (it stores only provider metadata, not key values).
