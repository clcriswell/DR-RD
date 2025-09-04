# Agent Trace Formats

The provenance layer records nested spans with `start_span`/`end_span`.
Utilities in `core.trace_export` can render these events as:

- **Span Tree** – hierarchical JSON tree.
- **Speedscope JSON** – for [speedscope.app](https://www.speedscope.app/).
- **Chrome Trace** – compatible with Chrome's tracing tools.

Each exporter accepts a list of events and produces the corresponding
structure. `write_exports` can persist all formats under a run directory.

## Trace Storage

Traces are written per run under `.dr_rd/runs/{run_id}/trace.json` using a
same-directory temporary file strategy. Writes are durable and atomic via
`os.replace` with a short retry loop. Any leftover `*.tmp.*` files older than an
hour can be removed safely with `utils.trace_writer.cleanup_stale_tmp`.
