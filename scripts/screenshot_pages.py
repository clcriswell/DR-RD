"""Capture configured pages using Playwright."""
import os
import sys
from typing import Any, Dict

import yaml
from playwright.sync_api import sync_playwright, Error


CONFIG_PATH = "docs/screenshots.yml"


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    config = load_config(CONFIG_PATH)
    base_url = os.getenv("APP_BASE_URL", config.get("base_url", "http://localhost:8501"))
    viewport = config.get("viewport", {"width": 1440, "height": 900})
    wait_ms = config.get("wait_ms", 0)
    pages = config.get("pages", [])

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        try:
            for entry in pages:
                url = base_url + entry["path"]
                try:
                    page.goto(url, wait_until="networkidle")
                except Error as e:  # navigation failure
                    print(f"Navigation failed for {url}: {e}", file=sys.stderr)
                    return 1
                if wait_ms:
                    page.wait_for_timeout(wait_ms)
                wait_for = entry.get("wait_for")
                if wait_for:
                    try:
                        page.wait_for_selector(wait_for, timeout=wait_ms or 30000)
                    except Error as e:
                        print(f"Missing selector {wait_for} for {url}: {e}", file=sys.stderr)
                        return 1
                out_path = entry["out"]
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                page.screenshot(path=out_path, full_page=True)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
