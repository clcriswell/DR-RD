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
    required = ["index.faiss", "docs.json"]
    missing = [f for f in required if not (bundle_dir / f).exists()]
    if missing:
        print(f"Missing required files: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(1)

    try:
        _, doc_count, dims = build_default_retriever(str(bundle_dir))
    except FAISSLoadError as e:
        print(f"Bundle load failed: {e}", file=sys.stderr)
        raise SystemExit(1)

    if doc_count == 0:
        print("Doc count is zero", file=sys.stderr)
        raise SystemExit(1)

    files = sorted(p.name for p in bundle_dir.iterdir() if p.is_file())
    manifest = {
        "path": str(bundle_dir),
        "doc_count": doc_count,
        "dims": dims,
        "files": files,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": None,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)

    print(f"doc_count={doc_count} dims={dims}")


if __name__ == "__main__":  # pragma: no cover
    main()
