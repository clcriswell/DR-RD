.PHONY: audit repo-map repo-validate

audit:
	pytest -q tests/audit

repo-map:
	python scripts/generate_repo_map.py

repo-validate:
	python scripts/validate_repo_map.py
