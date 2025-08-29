# Conda Packaging

This directory contains a lightweight Conda recipe for `dr-rd`.

## Building Locally

```bash
conda build conda -c conda-forge
```

The recipe pulls the version from the `GIT_DESCRIBE_TAG` environment variable. Extras are mapped to optional features in `meta.yaml`.

Artifacts are not uploaded automatically; inspect the output in `conda-bld/` and upload manually if desired.
