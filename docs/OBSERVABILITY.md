# Observability

This repository emits OpenTelemetry traces for runs, phases, steps, and model
calls. Tracing is enabled by default and gracefully degrades to a local JSONL
log when the OpenTelemetry SDK is not installed.

## Enabling OpenTelemetry

Tracing is controlled by environment variables:

- `DRRD_OTEL_ENABLED` (default `1`): disable by setting to `0`.
- `OTEL_EXPORTER_OTLP_ENDPOINT`: HTTP collector endpoint for OTLP span export.
- `DRRD_OTEL_CONSOLE` (default `0`): set to `1` to always emit console spans.

When the SDK is present and an OTLP endpoint is configured, spans are exported
using a `BatchSpanProcessor`. If the SDK is missing or tracing is disabled,
span records are appended to `.dr_rd/otel/spans.jsonl`.

## Span taxonomy

Spans nest to reflect the execution pipeline:

```
run
  ├─ phase.planner
  │   └─ step.planner
  ├─ phase.executor
  │   └─ step.executor (per task)
  └─ phase.synth
      └─ step.synth
```

LLM provider calls appear as `llm.call` spans under their respective steps.

## Correlation

Telemetry events and structured errors automatically include `trace_id` and
`span_id` when available. These identifiers can be used to correlate logs with
traces in external systems.

## Viewing traces

To view traces, point `OTEL_EXPORTER_OTLP_ENDPOINT` to a collector such as
Tempo, Jaeger, or the OpenTelemetry Collector. Without an endpoint, spans are
written to `.dr_rd/otel/spans.jsonl`, which can be inspected with standard
JSON tools.
