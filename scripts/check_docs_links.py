#!/usr/bin/env python3
"""Check docs for allowed and live links."""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
ALLOWED_HOSTS = {
    "streamlit.io",
    "docs.streamlit.io",
    "raw.githubusercontent.com",
    "github.com",
}
LINK_RE = re.compile(r"https?://[^)\s]+")


def main() -> int:
    no_net = os.environ.get("NO_NET") == "1"
    bad = False
    for path in DOCS_DIR.glob("*.md"):
        text = path.read_text()
        for match in LINK_RE.findall(text):
            host = urlparse(match).netloc
            if host not in ALLOWED_HOSTS:
                print(f"{path}: disallowed link {match}")
                bad = True
                continue
            if no_net:
                continue
            try:
                resp = requests.head(match, timeout=5, allow_redirects=True)
                if resp.status_code >= 400:
                    print(f"{path}: link {match} returned {resp.status_code}")
                    bad = True
            except Exception as exc:
                print(f"{path}: link {match} failed: {exc}")
                bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
