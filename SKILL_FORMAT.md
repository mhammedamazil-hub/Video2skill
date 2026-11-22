# Video2Skill — Skill Format

Video2Skill skills use the open SKILL.md format (Anthropic's Agent Skills
standard): a folder containing a SKILL.md file with YAML frontmatter and a
Markdown body, plus optional bundled files. Skills produced by Video2Skill are
portable across Claude Code, OpenAI Codex, Cursor, Gemini CLI, and other
compatible agent environments.

## Skill package layout

```
<skill-name>/
├── SKILL.md            # required: YAML frontmatter + instructions
├── skill.json          # manifest (id, name, version, status, capability, ...)
├── sas.json            # Skill Acquisition Specification (source of truth)
├── evidence/           # source evidence (frames, transcript, timeline)
├── scripts/            # generated helper scripts (run, not loaded)
└── versions/           # archived historical versions (never silently overwritten)
```

## SKILL.md frontmatter

```yaml
---
name: create-a-basic-3d-cube-and-apply-a-material-in-blender
description: Learn create a basic 3D cube ... from <source> via Video2Skill.
allowed-tools: Read
metadata:
  source: https://youtube.com/watch?v=...
  generated_by: video2skill
  domain: 3D modeling
  software: Blender
  software_version: 4.0
---
```

- `name` — required, lowercase, hyphenated, matches the folder name.
- `description` — required, what the skill does and when to use it.
- `allowed-tools` — optional, tools pre-approved while the skill is active.
- `metadata` — optional, arbitrary key-values (source, generated_by, domain,
  software, software_version).

## Body

The Markdown body contains:

- Source (video/file, goal, domain, software, version, OS)
- Preconditions
- Required tools
- Procedure (numbered steps, each citing timestamp `t=MM:SS` and frame evidence)
- Final result
- Error recovery
- Verification instructions
- Evidence section

Every step cites its source timestamp and frame evidence from the video.

## skill.json manifest

```json
{
  "id": "skill-create-a-basic-3d-cube...",
  "name": "create-a-basic-3d-cube...",
  "description": "...",
  "version": "0.1.0",
  "status": "draft",
  "source": "...",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "capability": { ... SAS ... },
  "procedure": { ... },
  "evaluation_history": [ ... ],
  "created_at": "...",
  "updated_at": "..."
}
```

- `status`: draft | verified | failed | archived.
- A verified skill never loses verification silently after modification; any
  changed version is reset to `draft` and must undergo regression testing.

## Versioning

Versions are semantic (major.minor.patch). The Evolution Agent bumps the patch
version on each revision and archives the previous full package under
`versions/<timestamp>` before any change. Duplicate detection, version
comparison, rollback, skill dependencies, and composition are supported by the
library.
