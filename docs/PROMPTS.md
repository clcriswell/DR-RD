# Prompt Registry

Prompts live in `prompts/*.yaml` and follow this schema:

```yaml
id: planner
version: "1.0.0"  # semver
title: "Planner system prompt"
description: "Task planning instructions for DR RD."
vars:
  - name: tone
    required: false
    default: concise
  - name: knowledge_hint
    required: false
    default: ""
template: |
  You are the Planner. Produce a minimal plan.
  Tone: {tone}
  {knowledge_hint}
changelog:
  - "1.0.0: Initial prompt."
```

Required keys are `id`, `version`, and `template`. Placeholders `{name}` must match entries in `vars`. Plain Python format strings are used and values are escaped to avoid code execution.

## Rendering

Use `utils.prompts.runtime.render(id, values)` to render a prompt and obtain a pin:

```python
text, pin = runtime.render("planner", {"tone": "casual"})
```

The `pin` contains `id`, `version`, and a content hash. `get_prompt_text(role, cfg)` resolves role aliases, applies defaults, and returns `(text, pin)`.

## Versioning

Semantic versions are bumped with `utils.prompts.versioning.next_version(cur, part)` where `part` is `patch`, `minor`, or `major`. `is_upgrade(old, new)` checks ordering. `unified_diff(old, new)` returns a unified diff string.

## CLI Utilities

- `scripts/prompt_lint.py` validates all prompt files.
- `scripts/prompt_bump.py --id planner --part minor` updates the version and appends a timestamped changelog line.
- `scripts/prompt_diff.py --id planner --old 1.0.0` shows a diff against a tagged version.

## Pins in Runs

Runs record the exact prompt versions used. `run_config.lock.json` contains a `prompts` block with pins and `run_meta.json` mirrors this for quick lookup. This enables reproducible executions.
