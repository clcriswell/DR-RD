import argparse
import math
import re
import sys
from pathlib import Path

TOKEN_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "openai_key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "aws_key"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._-]{10,}"), "bearer_token"),
]

EXCLUDE_DIRS = {".dr_rd", "node_modules"}


def shannon_entropy(s: str) -> float:
    """Compute Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = {c: s.count(c) for c in set(s)}
    n = len(s)
    return -sum((f / n) * math.log2(f / n) for f in freq.values())


def scan_file(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, 1):
                for rx, name in TOKEN_PATTERNS:
                    if rx.search(line):
                        findings.append((lineno, name))
                for token in re.findall(r"[A-Za-z0-9+/=_-]{20,}", line):
                    if shannon_entropy(token) > 4.0:
                        findings.append((lineno, "high-entropy"))
    except Exception:
        pass
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repository for secrets")
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.path)
    hits: list[str] = []
    for p in root.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.is_file():
            for lineno, name in scan_file(p):
                rel = p.relative_to(root)
                hits.append(f"{rel}:{lineno}: {name}")

    for h in hits:
        print(h)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
