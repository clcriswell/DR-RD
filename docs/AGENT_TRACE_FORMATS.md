# Agent Trace Formats

The provenance layer records nested spans with `start_span`/`end_span`.
Utilities in `core.trace_export` can render these events as:

- **Span Tree** – hierarchical JSON tree.
- **Speedscope JSON** – for [speedscope.app](https://www.speedscope.app/).
- **Chrome Trace** – compatible with Chrome's tracing tools.

Each exporter accepts a list of events and produces the corresponding
structure. `write_exports` can persist all formats under a run directory.
