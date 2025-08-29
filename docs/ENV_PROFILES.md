# Environment Profiles

The project provides composable configuration profiles under `config/profiles/`.
Select a profile via the `DRRD_PROFILE` environment variable. Profiles merge
on top of the base configuration and expose feature flags, budgets and RAG
settings.

```bash
export DRRD_PROFILE=staging
```

Helm charts map the `profiles.profile` value to the same profile name so
cluster deployments reuse these configurations.
