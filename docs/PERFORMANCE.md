# Performance

This project aims to keep the Streamlit UI thin by deferring heavy imports until
runtime. Heavy libraries such as pandas, numpy and cloud SDKs are imported
lazily to improve cold start time.

## Baseline

- Cold start time to import `app`: ~2.4s on a development machine.

## After lazy imports

- Cold start time: ~1.6s
- No heavy libraries are imported in `app/` or `pages/` at module import time.

## Rules

- Avoid top level imports of pandas, numpy, cloud SDKs or LLM SDKs in `app/` and
  `pages/`.
- Use `utils.lazy_import.lazy` for module level laziness and
  `utils.lazy_import.local_import` for function scoped imports.

## Profiling imports

Run a quick profile of import times:

```bash
python -X importtime -c "import runpy; runpy.run_module('app', run_name='__main__')" 2> importtime.log
python scripts/profile_imports.py importtime.log --top 30
```
