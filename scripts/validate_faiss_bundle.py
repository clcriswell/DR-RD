#!/usr/bin/env python3
"""Validate a FAISS index bundle and emit a manifest."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from knowledge.faiss_store import FAISSLoadError, build_default_retriever


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".faiss_index", help="bundle directory")
    ap.add_argument("--out", default="manifest.json", help="output manifest path")
    args = ap.parse_args()

    bundle_dir = Path(args.path)
    files = sorted(p.name for p in bundle_dir.iterdir() if p.is_file()) if bundle_dir.exists() else []

    doc_count = 0
    dims = 0
    loader_error = None
    validated_by = None

    try:
        _, doc_count, dims = build_default_retriever(str(bundle_dir))
        validated_by = "runtime_loader"
    except FAISSLoadError as e:
        loader_error = str(e)

    if validated_by is None:
        patterns = [
            {"index.faiss", "docs.json"},
            {"index.faiss", "docstore.pkl"},
            {"index.pkl", "docstore.pkl"},
            {"faiss.index", "docstore.json"},
            {"index.bin", "metadatas.json"},
        ]
        file_set = set(files)
        if any(patt.issubset(file_set) for patt in patterns):
            validated_by = "file_pattern"
        else:
            print(
                f"Bundle at {bundle_dir} not loadable and no known pattern matched",
                file=sys.stderr,
            )
            raise SystemExit(1)

    manifest = {
        "path": str(bundle_dir),
        "doc_count": doc_count,
        "dims": dims,
        "files": files,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": None,
        "loader_error": loader_error,
        "validated_by": validated_by,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)

    print(f"doc_count={doc_count} dims={dims}")


if __name__ == "__main__":  # pragma: no cover
    main()
