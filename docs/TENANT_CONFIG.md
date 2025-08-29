# Tenant Configuration Overlays

Tenant specific configuration overlays live outside the repository under
`config/tenants/<org>/<workspace>/`. These files are git-ignored and may contain
partial YAML fragments for supported config files such as `budgets.yaml`,
`models.yaml`, `rag.yaml`, `reporting.yaml` and `telemetry.yaml`.

Overlay precedence (lowest to highest):
1. Base config in `config/*.yaml`
2. Profile overlay in `config/profiles/<profile>/<name>.yaml`
3. Tenant overlay in `config/tenants/<org>/<workspace>/<name>.yaml`
4. Environment variable `DRRD_CONFIG_<NAME>` containing YAML

The helper `dr_rd.config.loader.load_config()` performs this merge and is used by
subsystems needing tenant aware settings.
