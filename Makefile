.PHONY: init lint type test cov perf docs map repo-map repo-validate audit audit-tests lock licenses sbom build repro release-checklist

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

audit-tests:
	pytest -q tests/audit

lock:
	pip-compile --allow-unsafe --generate-hashes --output-file=requirements.lock.txt requirements.in
	pip-compile --allow-unsafe --generate-hashes --output-file=dev-requirements.lock.txt dev-requirements.in

licenses:
	mkdir -p reports
	pip-licenses --format=json --output-file reports/licenses.json
	python scripts/check_licenses.py --input reports/licenses.json

audit:
	mkdir -p reports
	pip-audit -r requirements.lock.txt --format json --output reports/pip-audit.json || true
	python scripts/gate_pip_audit.py --input reports/pip-audit.json

sbom:
        python scripts/gen_sbom.py

build:
        python scripts/build_artifacts.py

repro:
        python scripts/repro_check.py

release-checklist:
	@echo "build"
	@echo "sbom"
	@echo "release"
