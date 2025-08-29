# Supply Chain

See also the [Open Source Policy](OPEN_SOURCE_POLICY.md),
[Release Security](RELEASE_SECURITY.md), and the [SBOM guide](../sbom/README.md).

## Reproducible Builds
To make release artifacts deterministic we build under a fixed environment:

- `SOURCE_DATE_EPOCH`
- `PYTHONHASHSEED=0`
- `TZ=UTC`
- `LC_ALL=C`
- `LANG=C`

Run `make build` to produce the sdist and wheel. The script writes
`reports/build/build_manifest.json` containing the commit, source date
epoch, and the SHA256 hash and size of each artifact.

`make repro` builds the project twice in isolated work directories with the
same deterministic environment. It compares the resulting artifact hashes
and writes `reports/build/repro_report.json`. If the hashes differ the script
normalizes archives and compares their contents; mismatches are reported but do
not fail the command. Gating will be introduced in a later phase.

## Release Gate
Tagged releases run `scripts/release_check.py` which enforces:

- CI is green on `main` (skipped if `GITHUB_TOKEN` is absent).
- Dependency locks are current.
- No HIGH/CRITICAL vulnerabilities unless `AUDIT_ALLOW_HIGH=1`.
- Third-party licenses pass `scripts/check_licenses.py`.
- `sbom/cyclonedx-python.json` was generated in the last 24 hours.
- `scripts/validate_config_lock.py` shows no drift.
- Performance is within 10% of `scripts/perf_baseline.json` unless `PERF_ALLOW_REGRESSION=1`.
- `repo_map.yaml` and `docs/REPO_MAP.md` have no pending changes.
- `CHANGELOG.md` contains entries under Unreleased and the version matches the tag.

Temporary overrides require justification:

- `AUDIT_ALLOW_HIGH=1` – allow high/critical vulnerabilities.
- `PERF_ALLOW_REGRESSION=1` – allow >10% performance regression.

## Secret Scanning
The `secret-scan` workflow runs [Gitleaks](https://github.com/gitleaks/gitleaks)
on every push, pull request, manual trigger, and a weekly schedule. Findings are
uploaded as SARIF to GitHub Code Scanning and preserved as workflow artifacts.
Run `make secrets-scan` locally to generate `reports/security/gitleaks.sarif`
before opening a pull request.

## Where to find reports

- `reports/licenses.json` – license inventory for third-party packages.
- `reports/pip-audit.json` – vulnerability scan results.
- `reports/security/gitleaks.sarif` – secrets scan findings.
- `reports/build/build_manifest.json` – hashes for built artifacts.
- `reports/build/repro_report.json` – reproducible build comparison.
