# Packaging

## Build

```bash
python -m build
```

## Install with Extras

```bash
pip install .[ui,connectors,reporting]
```

## CLI Usage

```bash
dr-rd --version
dr-rd demo specialists
dr-rd app  # launches Streamlit
```

## Publish

Publishing is handled via `release.yml` and `publish-pypi.yml`. Tag releases with `v*` to trigger the workflows.
