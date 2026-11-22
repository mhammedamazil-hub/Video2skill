# Video2Skill — Test Report

## Verified functionality (end-to-end)

All commands were tested in a clean environment with
`VIDEO2SKILL_CONFIG_DIR` pointed at a temporary directory.

| Command | Result |
|---|---|
| `video2skill init` | Bootstraps Python venv, creates config + library; reports missing ffmpeg/yt-dlp |
| `video2skill config provider` | Enables a provider, sets default model, writes config.json |
| `video2skill config show` | Prints full configuration |
| `video2skill doctor` | Reports Node/Python/FFmpeg/yt-dlp/engine/config/provider status |
| `video2skill learn <url>` | Runs discovery interview, computes readiness, generates draft skill + SKILL.md |
| `video2skill list` | Lists skills in library with version and status |
| `video2skill inspect <skill>` | Prints manifest metadata + SKILL.md body |
| `video2skill test <skill>` | Runs examination; gracefully reports "not configured" when no API key |
| `video2skill evolve <skill>` | Archives prior version, bumps version, records changes |

### Discovery interview test

A 13-question interview (Blender cube + material tutorial) reached
**100% readiness** (threshold 95%), gate met, and produced a draft skill
package with SKILL.md and manifest saved to the library.

### Evolution test

A skill with recorded failure history was evolved: version `0.1.0` archived
under `versions/<timestamp>`, version bumped to `0.1.1`, status reset to
`draft` requiring re-verification.

## Known limitations

- FFmpeg, yt-dlp, Whisper, and tesseract are external dependencies. Video
  ingestion produces real evidence only when present; discovery proceeds from
  the user interview without them.
- Model provider adapters require real API keys for learner examinations.
  Without keys, examination reports "not configured" rather than fabricating
  results (no fake evaluation).
- Sandboxing uses bubblewrap on Linux when available; otherwise execution is
  refused. macOS Seatbelt / Windows AppContainer drivers are specified but the
  reference implementation ships bubblewrap + refuse-fallback.
- The discovery output is emitted once by the CLI (duplicate print fixed).

## Test environment

- Node.js v22.22.3, npm 10.9.8, TypeScript 5.9.3
- Python 3.11.2
- Linux x64

## How to run

```bash
cd /home/user/Video2skill
npm install
npm run build
node dist/cli/index.js help
# set VIDEO2SKILL_CONFIG_DIR to a temp dir for isolated testing
```

## To complete

- Add automated unit tests under `packages/cli/src/**/*.test.js` and run with
  `node --test`.
- Test a complete acquisition workflow using an authorized sample video (once
  FFmpeg + yt-dlp + Whisper are available).
- Test both learner types using independent contexts (requires two configured
  providers with API keys).
- Test `npx video2skill` installation in a clean environment after publishing
  to npm.
