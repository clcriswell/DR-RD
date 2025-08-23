# Contributing

## Formatting

This project uses [Black](https://github.com/psf/black) version 24.8.0 for code formatting.

Format your code locally before committing:

```bash
pip install -r requirements-dev.txt
black .
```

Optional: enable [pre-commit](https://pre-commit.com/) hooks for automatic formatting and linting:

```bash
pip install pre-commit
pre-commit install
pre-commit run -a
```

Continuous integration runs Black on changed Python files and will fail if they need reformatting.
