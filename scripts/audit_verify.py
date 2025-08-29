from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import audit_log


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Verify audit log hash chain")
    p.add_argument("path")
    args = p.parse_args(argv)
    path = Path(args.path)
    ok = audit_log.verify_chain(path)
    count = sum(1 for _ in path.open()) if path.exists() else 0
    print(json.dumps({"ok": ok, "entries": count}))


if __name__ == "__main__":
    main()
