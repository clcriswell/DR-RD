#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

SAFE_OVERRIDES = {
    "RAG_ENABLED": "0",
    "ENABLE_LIVE_SEARCH": "0",
    "EVALUATORS_ENABLED": "0",
    "MODEL_ROUTING_ENABLED": "0",
    "SAFETY_ENABLED": "1",
}


def main(path: str) -> None:
    env_path = Path(path)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v
    existing.update(SAFE_OVERRIDES)
    with open(env_path, "w", encoding="utf-8") as fh:
        for k, v in existing.items():
            fh.write(f"{k}={v}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".env.flags")
    args = ap.parse_args()
    main(args.path)
