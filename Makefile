.PHONY: init lint type test cov perf docs map repo-map repo-validate audit

init:
	pip install -e .[dev]
	pre-commit install

lint:
	ruff check .
	black --check .

type:
	mypy dr_rd core app

test:
	pytest -q --maxfail=1 --disable-warnings

cov:
	pytest --cov=dr_rd --cov=core --cov=app --cov-report=xml

perf:
	PERF_MODE=1 pytest tests/perf/test_perf_budget.py -q

docs:
	markdown-link-check docs/INDEX.md
	python -m scripts.lint_docs

map repo-map:
	python scripts/generate_repo_map.py

repo-validate:
	python scripts/validate_repo_map.py

audit:
	pytest -q tests/audit
