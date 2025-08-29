# Supply Chain

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
