# Rollback Playbook

1. Identify last known good tag with `git tag`.
2. Run `scripts/rollback_release.py` to get instructions.
3. Verify config lock and restart smoke tests.
4. If rollback fails, reopen the incident.
