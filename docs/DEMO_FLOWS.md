# Demo Flows

Each flow reads from `samples/tasks/` and writes JSON and Markdown summaries.

## Materials
```
python scripts/demo_run.py --flow materials --out samples/runs/<stamp>
```

## QA
```
python scripts/demo_run.py --flow qa --out samples/runs/<stamp>
```

## Finance
```
python scripts/demo_run.py --flow finance --out samples/runs/<stamp>
```

## Compliance
```
python scripts/demo_run.py --flow compliance --out samples/runs/<stamp>
```

## Dynamic
```
python scripts/demo_run.py --flow dynamic --out samples/runs/<stamp>
```

Flags such as `RAG_ENABLED=0` can be passed via `--flags`.
