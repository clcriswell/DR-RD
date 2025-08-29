.PHONY: init lint type test cov perf docs map repo-map repo-validate audit audit-tests lock licenses sbom build repro supply-chain release-check release-checklist gtm housekeeping

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

secrets-scan:
	mkdir -p reports/security
	gitleaks detect --source . --redact --config=.gitleaks.toml --report-format sarif --report-path reports/security/gitleaks.sarif
	@echo "Gitleaks report written to reports/security/gitleaks.sarif"

build:
	python scripts/build_artifacts.py

repro:
	python scripts/repro_check.py

supply-chain: licenses audit sbom repro
	@echo "License report: reports/licenses.json"
	@echo "Vulnerability report: reports/pip-audit.json"
	@echo "SBOM: sbom/cyclonedx-python.json"
	@echo "Repro report: reports/build/repro_report.json"

release-check:
#       AUDIT_ALLOW_HIGH=1 to allow high/critical vulnerabilities
#       PERF_ALLOW_REGRESSION=1 to permit >10% perf regression
	python scripts/release_check.py

release-checklist:
        @echo "build"
        @echo "sbom"
        @echo "release"

gtm:
        STAMP=$$(date +%Y%m%d_%H%M%S); \
        python scripts/demo_run.py --flow all --out samples/runs/$$STAMP --flags RAG_ENABLED=0,EVALUATORS_ENABLED=1; \
        python scripts/snapshots.py --runs samples/runs/$$STAMP --out docs/assets/screens; \
        python scripts/generate_deck.py --outline docs/templates/deck_outline.yaml --shots docs/assets/screens --out docs/kits

housekeeping:
        python scripts/stale_code_scan.py
        python scripts/dead_link_check.py --internal-only
        python scripts/generate_repo_map.py
