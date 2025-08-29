# Open Source Policy

This project follows a simple open-source license policy.

## Allow
- MIT
- BSD-2-Clause
- BSD-3-Clause
- Apache-2.0
- MPL-2.0

## Warn (manual review)
- LGPL-2.1
- LGPL-3.0
- EPL-2.0

## Deny
- AGPL-3.0
- GPL-3.0 (unless an explicit written exemption is granted)

All dependencies must be pinned via `*.lock.txt` files with hashes.

## Secret Scanning
We use [Gitleaks](https://github.com/gitleaks/gitleaks) to prevent committing secrets.
The default CI workflow blocks on any findings. In exceptional cases, set
`GITLEAKS_ALLOW_FINDINGS=1` to allow the workflow to pass, and include a
justification in the pull request description.

To extend the allowlist in `.gitleaks.toml`, add entries under
`[allowlist].paths` for additional directories, `regexes` for safe patterns, or
populate the `commits` array with specific SHAs for historical false positives.
