# Video2Skill — Agent Integration Guide

Video2Skill-generated skills use the open SKILL.md format and install into
Claude Code, OpenAI Codex, Cursor, Gemini CLI, and other compatible agent
environments — the same way skills from skills.sh install.

## How a host agent invokes Video2Skill

A generated skill instructs the host agent how to invoke the local engine:

```
Use Video2Skill to learn Blender procedural modeling from this tutorial.
→ Run: video2skill learn "<VIDEO_URL>"
→ Then: video2skill test <skill-name>
→ Review the evaluation report, then install this SKILL.md into this agent.
```

The host agent should:
1. Detect whether the local `video2skill` engine is available (`video2skill doctor`).
2. Offer to run `video2skill learn <video>` for a new capability.
3. Offer to run `video2skill test <skill-name>` to verify an existing skill.
4. Load the generated SKILL.md when a task matches the skill's description.

## Per-agent integration

### Claude Code

Install a Video2Skill skill into Claude Code:

```bash
npx skills add <owner>/video2skill-<skill-name>
# or copy the skill folder into ~/.claude/skills/
```

Claude Code reads only each skill's frontmatter (`name`, `description`) at
startup (~100 tokens) and loads the full SKILL.md body when a task matches.

### OpenAI Codex / Cursor / Gemini CLI

These agents also consume SKILL.md folders. Place the skill folder in the
agent's skill directory and reference it by name. Each agent has its own
convention for skill directories and frontmatter handling — Video2Skill emits
the portable base format (name, description, allowed-tools, metadata) plus
agent-specific sidecars where needed.

Do not assume all agents use identical directories or frontmatter; dedicated
adapters live in `integrations/`.

## Natural invocation example

User: "Use Video2Skill to learn Blender procedural modeling from this tutorial."

Agent response: runs `video2skill learn <url>`, guides the user through the
discovery interview, confirms the 95% readiness gate, generates the skill, runs
`video2skill test <skill-name>` for same-model and cross-model learners, then
installs the SKILL.md into the agent.

## Permissions

The host agent must not execute arbitrary commands without permission.
Video2Skill operations (especially `learn` and `test`) should be confirmed by
the user before running, and sandboxed execution is used for skill steps.
