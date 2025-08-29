# Helm Quickstart

The chart under `deploy/helm/dr-rd` deploys the Streamlit app and runner
worker. Key values in `values.yaml`:

- `image` / `workerImage` – container repositories and tags.
- `featureFlags` – maps to application feature flags.
- `profiles.profile` – selects a config profile.
- `pvc` – persistent volume for `.dr_rd` data.

Render templates with:

```bash
helm template dr-rd deploy/helm/dr-rd
```
