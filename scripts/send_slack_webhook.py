#!/usr/bin/env python3
import json
import os
import sys
import urllib.request


def main(summary_path: str) -> None:
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        print("SLACK_WEBHOOK_URL not set; skipping")
        return
    with open(summary_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    urllib.request.urlopen(req, json.dumps(data).encode("utf-8"))


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "ops_report.json"
    main(path)
