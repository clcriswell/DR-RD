#!/usr/bin/env python3
import json
import os
import sys


def main(summary_path: str) -> None:
    token = os.getenv("GITHUB_TOKEN")
    with open(summary_path, "r", encoding="utf-8") as fh:
        summary = json.load(fh)
    title = summary.get("title", "Ops Alert")
    body = json.dumps(summary, indent=2)
    if not token:
        print("GITHUB_TOKEN not set; printing summary only")
        print(body)
        return
    print(f"Would create/update GitHub issue with title: {title}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "ops_report.json"
    main(path)
