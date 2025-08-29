# Contributing

Thanks for considering a contribution. See [docs/CONTRIBUTING_QUICKSTART.md](docs/CONTRIBUTING_QUICKSTART.md) for the fastest path to your first PR.

## Development flow
- Install deps with `make init`.
- Run `make lint type test` before pushing.
- Regenerate the repo map with `make repo-map` when code moves.
- Use `pre-commit run --files <files>` for formatting and link checks.
- Keep commits focused and reference issues when applicable.
- Run demos offline with `python scripts/demo_run.py`.

## Commit style
- Use conventional commits when possible.
- Include tests for new behavior.
