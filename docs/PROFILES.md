# Profiles

Profiles let you save named presets for the run form so common settings are one click away. Each profile stores only non‑secret knobs such as mode, provider/model, budgets, token limits, retrieval and safety flags, knowledge source IDs, and feature flags.

## Managing Profiles
- **Create:** Configure the run form then use *Save current as profile* and supply a name.
- **Apply:** Pick a profile from the dropdown on the main page or from the Profiles page. Applying a profile updates form fields but never overwrites free‑text idea inputs.
- **Delete / Rename / Edit:** Visit the Profiles page from the sidebar to manage existing profiles. Edits use a raw JSON view with validation.
- **Default:** Set a profile as default from the Profiles page. The default (or last used) profile preselects on next load.

## Query Parameter and CLI
- The main page accepts `?profile=name` to prefill the run form for reproducible links.
- The CLI supports `--profile NAME` which applies the profile before other flags.

## Tips
Create multiple presets such as **fast-mini** for quick inexpensive runs, **quality-sonnet** for higher quality results, or **strict-safety** when reviewing sensitive content.
