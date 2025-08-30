from __future__ import annotations

"""Migrate artifacts between storage backends."""

import argparse

from utils.storage import _create_storage

PREFIX_MAP = {
    "runs": "runs",
    "knowledge": "knowledge/uploads",
    "all": "",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", choices=["local", "s3", "gcs"], required=True)
    ap.add_argument("--to", dest="dst", choices=["local", "s3", "gcs"], required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prefix", choices=["runs", "knowledge", "all"], default="all")
    args = ap.parse_args()

    src = _create_storage({"backend": args.src})
    dst = _create_storage({"backend": args.dst})
    prefix = PREFIX_MAP[args.prefix]
    total = 0
    for ref in src.list(prefix):
        data = src.read_bytes(ref.key)
        if not args.dry_run:
            dst.write_bytes(ref.key, data)
            dst_size = dst.read_bytes(ref.key)
            if len(dst_size) != len(data):
                print("mismatch", ref.key)
                return 1
        total += 1
    print(f"copied {total} objects")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
