#!/usr/bin/env python3
"""Upload a local FAISS index bundle to Google Cloud Storage."""

from __future__ import annotations

import argparse
from pathlib import Path


def _parse_gs_uri(uri: str) -> tuple[str, str]:
    rem = uri[5:] if uri.startswith("gs://") else uri
    bucket, _, prefix = rem.partition("/")
    return bucket, prefix


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".faiss_index", help="local bundle directory")
    ap.add_argument("--dst", required=True, help="gs://bucket/prefix")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.exists():  # pragma: no cover - simple arg check
        raise SystemExit(f"src {src} not found")
    if not args.dst.startswith("gs://"):
        raise SystemExit("dst must be gs://bucket/prefix")

    bucket, prefix = _parse_gs_uri(args.dst)
    from google.cloud import storage  # type: ignore

    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    for path in src.rglob("*"):
        if path.is_file():
            rel = path.relative_to(src).as_posix()
            blob = bucket_obj.blob(f"{prefix.rstrip('/')}/{rel}")
            blob.upload_from_filename(path)
            print(f"Uploaded {rel}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
