from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT = Path("docs/assets/fonts/DejaVuSansMono.ttf")


def render(json_path: Path | None, md_path: Path | None, out_path: Path) -> None:
    text = ""
    if json_path and json_path.exists():
        text += json.dumps(json.loads(json_path.read_text()), indent=2)
    if md_path and md_path.exists():
        text += "\n" + md_path.read_text()
    img = Image.new("RGB", (1000, 800), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(FONT), 14)
    draw.text((10, 10), text[:2000], fill="black", font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


PRESETS = ["materials", "qa", "finance", "compliance", "dynamic", "trace"]


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--runs", required=True, help="Run directory with JSON/MD")
    p.add_argument("--out", required=True, help="Output directory for PNGs")
    args = p.parse_args(argv)

    run_dir = Path(args.runs)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in PRESETS:
        json_path = run_dir / f"{name}.json"
        md_path = run_dir / f"{name}.md"
        render(json_path if json_path.exists() else None, md_path if md_path.exists() else None, out_dir / f"{name}.png")
    print(f"Screenshots written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
