"""Compute visual diffs between baseline and candidate images."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

from PIL import Image, ImageChops


@dataclass
class DiffResult:
    file: str
    ratio: float
    status: str


def diff_ratio(baseline: str, candidate: str) -> float:
    """Return the ratio of changed pixels between two images."""
    with Image.open(baseline).convert("RGBA") as b_img, Image.open(candidate).convert(
        "RGBA"
    ) as c_img:
        if b_img.size != c_img.size:
            c_img = c_img.resize(b_img.size)
        diff = ImageChops.difference(b_img, c_img)
        diff_data = diff.getdata()
        changed = sum(1 for px in diff_data if px != (0, 0, 0, 0))
        total = b_img.size[0] * b_img.size[1]
        return changed / total


def compute_diffs(
    baseline_dir: str, candidate_dir: str, out_dir: str, threshold: float
) -> Tuple[List[DiffResult], bool]:
    os.makedirs(out_dir, exist_ok=True)
    results: List[DiffResult] = []
    exceeds = False
    for name in os.listdir(baseline_dir):
        b_path = os.path.join(baseline_dir, name)
        c_path = os.path.join(candidate_dir, name)
        if not os.path.exists(c_path):
            continue
        ratio = diff_ratio(b_path, c_path)
        status = "changed" if ratio > threshold else "ok"
        if ratio > threshold:
            with Image.open(b_path).convert("RGBA") as b_img, Image.open(c_path).convert(
                "RGBA"
            ) as c_img:
                diff = ImageChops.difference(b_img, c_img)
                diff.save(os.path.join(out_dir, name.replace(".png", "_diff.png")))
            exceeds = True
        results.append(DiffResult(file=name, ratio=ratio, status=status))
    return results, exceeds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-dir", default="docs/images")
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.01)
    args = parser.parse_args()

    results, exceeds = compute_diffs(
        args.baseline_dir, args.candidate_dir, args.out_dir, args.threshold
    )

    summary = [r.__dict__ for r in results]
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f)

    print("| file | change % | status |")
    print("| --- | --- | --- |")
    for r in results:
        print(f"| {r.file} | {r.ratio*100:.2f}% | {r.status} |")

    return 1 if exceeds else 0


if __name__ == "__main__":
    sys.exit(main())
