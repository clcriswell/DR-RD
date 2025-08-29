#!/usr/bin/env python3
"""Scan markdown files for dead links."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

import requests

LINK_RE = re.compile(r"\[.+?\]\(([^)]+)\)")
HEADER_RE = re.compile(r"^(#+)\s+(.*)", re.MULTILINE)


def slugify(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9\- ]", "", text).lower().strip()
    return re.sub(r"\s+", "-", text)


def extract_links(text: str) -> Sequence[str]:
    return LINK_RE.findall(text)


def extract_anchors(text: str) -> set[str]:
    return {slugify(m[1]) for m in HEADER_RE.findall(text)}


def check_internal(link: str, current: Path) -> tuple[bool, str]:
    target, anchor = (link.split("#", 1) + [""])[0:2]
    target_path = (current.parent / target).resolve()
    if not target_path.exists():
        return False, f"missing file: {target}"
    if anchor:
        anchors = extract_anchors(target_path.read_text())
        if slugify(anchor) not in anchors:
            return False, f"missing anchor: {anchor}"
    return True, ""


def head(url: str) -> int:
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        return resp.status_code
    except Exception:
        return 0


def check_links(
    files: Iterable[Path],
    allowlist: set[str] | None = None,
    denylist: set[str] | None = None,
    internal_only: bool = False,
) -> dict:
    allowlist = allowlist or set()
    denylist = denylist or set()
    internal_errors: list[dict] = []
    external_warnings: list[dict] = []
    external_candidates: list[tuple[str, Path]] = []
    for file in files:
        text = Path(file).read_text()
        for link in extract_links(text):
            if link.startswith("http://") or link.startswith("https://"):
                if internal_only:
                    continue
                domain = re.sub(r"^https?://([^/]+).*", r"\1", link)
                if allowlist and domain not in allowlist:
                    continue
                if denylist and domain in denylist:
                    continue
                external_candidates.append((link, Path(file)))
            else:
                ok, reason = check_internal(link, Path(file))
                if not ok:
                    internal_errors.append({"file": str(file), "link": link, "reason": reason})
    if not internal_only and external_candidates:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = {ex.submit(head, url): (url, file) for url, file in external_candidates}
            for fut in concurrent.futures.as_completed(futures):
                url, file = futures[fut]
                status = fut.result()
                if status in {404, 429} or status >= 500 or status == 0:
                    external_warnings.append({"file": str(file), "url": url, "status": status})
    return {"internal_errors": internal_errors, "external_warnings": external_warnings}


def find_markdown_files() -> list[Path]:
    files = [Path("README.md")] + list(Path(".").glob("*.md")) + list(Path("docs").rglob("*.md"))
    return sorted({p.resolve() for p in files if p.exists()})


def main() -> int:
    parser = argparse.ArgumentParser(description="Check markdown for dead links.")
    parser.add_argument("files", nargs="*")
    parser.add_argument("--internal-only", action="store_true")
    parser.add_argument("--allowlist", default="")
    parser.add_argument("--denylist", default="")
    parser.add_argument("--json-output", default="dead_links.json")
    args = parser.parse_args()

    files = [Path(f) for f in args.files] if args.files else find_markdown_files()
    allow = {d for d in args.allowlist.split(",") if d}
    deny = {d for d in args.denylist.split(",") if d}
    results = check_links(files, allow, deny, args.internal_only)
    Path(args.json_output).write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if results["internal_errors"]:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
