# Example Bank

High quality agent runs are harvested into per-role example catalogs. `dr_rd.examples.harvest()` filters knowledge base records and `dr_rd.examples.catalog.refresh()` maintains `examples/<role>.jsonl` files sorted by quality score.

Future prompt registries can fetch exemplars via `dr_rd.examples.bridge_registry.get_examples(role, n)`.
