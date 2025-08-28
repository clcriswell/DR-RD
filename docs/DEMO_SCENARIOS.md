# Demo Scenarios

Offline demo scripts located under `scripts/demos/`.

## Specialists
```
python scripts/demos/demo_specialists.py
```

## Dynamic Agent
```
python scripts/demos/demo_dynamic.py
```

## Compliance
```
python scripts/demos/demo_compliance.py
```

## RAG Modes
```
python scripts/demos/demo_rag.py
```

Each script prints compact JSON with a non-empty `sources` list and exits non-zero if
required fields are missing. Flags such as `RAG_ENABLED` and `EVALUATORS_ENABLED`
are not required for these offline runs.
