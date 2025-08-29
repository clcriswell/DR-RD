# Versioning & LTS Policy

The project follows [SemVer](https://semver.org/). The public surface
includes:

- Agent I/O schemas (`dr_rd/schemas`)
- `PromptFactory` and `PromptRegistry` contracts
- `core.tool_router` interface

## LTS

Minor releases receive six months of support. After that window only
security fixes are backported. Patch releases do not extend LTS windows.

## CHANGELOG

- Maintain an `UNRELEASED` section at the top of `CHANGELOG.md`.
- Reference pull request numbers in entries.
- Document breaking changes, new features, and fixes separately.

See repository PR templates for guidance.
