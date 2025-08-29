# Compatibility Matrix

| Component          | Supported versions/notes |
| ------------------ | ------------------------ |
| Python             | 3.10, 3.11              |
| OS                 | Linux, macOS             |
| Provider SDKs      | OpenAI `>=1.0`          |

## Feature Flags

| Flag                 | Interactions |
| -------------------- | ------------ |
| `MODEL_ROUTING`       | Requires `PROVENANCE` for audit trails |
| `RAG_ENABLED`         | Enables retrieval; implies `PROVENANCE` |
| `EVALUATORS_ENABLED`  | Works with `TELEMETRY` for scoring logs |
| `SAFETY_ENABLED`      | Can be combined with `RAG_ENABLED` |
| `PROVENANCE`          | Independent; recommended always on |
| `TELEMETRY`           | Optional; augments evaluator reports |
