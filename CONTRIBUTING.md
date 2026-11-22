# Video2Skill — Contributing

Thank you for contributing! Video2Skill is an autonomous skill acquisition
engine; correctness, maintainability, reliability, and actual capability matter
more than file or line counts.

## How to contribute

1. Fork the repository and create a branch from `main`.
2. Implement real functionality (no fake agents, no simulated learning, no
   placeholder verification).
3. Write automated tests for new behavior.
4. Run the build and tests: `npm install && npm run build`.
5. Run diagnostics: `video2skill doctor`.
6. Update the relevant documentation (ARCHITECTURE, SKILL_FORMAT, PROVIDER_GUIDE,
   EVALUATION_METHODOLOGY, SECURITY, etc.).
7. Record known limitations in TEST_REPORT.md.
8. Open a pull request.

## Principles

- No hardcoded API keys. Secrets come from environment variables.
- No unrestricted generated-code execution; sandbox-first, refuse-if-unsafe.
- No unverified skill installation; changed versions undergo regression testing.
- No silent overwrites of verified skills; versions are archived.
- No LLM self-declared readiness or success; evidence-based scoring only.
- Prefer existing stable libraries over reinventing infrastructure.

## Reporting issues

Include: OS, Node version, Python version, `video2skill doctor` output, and
the command that failed. Do not include API keys or personal secrets.

## License

MIT. By contributing, you agree your contributions are licensed under MIT.
