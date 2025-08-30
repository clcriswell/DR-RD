# Documentation Index

## UI
- [Streamlit Capabilities](UI_RESEARCH.md)
- [UX Metrics](UX_METRICS.md)
- [UI Heuristic Audit](UI_AUDIT.md)
- [UI Upgrade Spec](UI_SPEC.md)
- Demo mode: use the **Run demo** button in the app to play back a sample run with local artifacts only—no network or billing.

## Utilities
- `scripts/cleanup_runs.py` — remove old run artifacts (`--keep N` or `--max-bytes M`)

## E2E tests
Run the Playwright end-to-end tests either against a locally started app or a deployed URL.

Local app:

```
APP_BASE_URL=http://localhost:8501 APP_EXTERNAL=0 \
pytest -q e2e
```

Against deployed app:

```
APP_EXTERNAL=1 APP_BASE_URL=https://dr-rnd.streamlit.app \
pytest -q e2e
```
