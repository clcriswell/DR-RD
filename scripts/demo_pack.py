from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="Run directory")
    p.add_argument("--flow", required=True, help="Flow name")
    p.add_argument("--out", default="samples/kits", help="Output directory")
    args = p.parse_args(argv)

    run_dir = Path(args.run)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"demo_{args.flow}_{stamp}.zip"

    manifest = {
        "flow": args.flow,
        "created": stamp,
        "files": [f.name for f in run_dir.glob("*")],
    }
    with open(run_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in run_dir.glob("*"):
            zf.write(file, arcname=file.name)
    print(f"Packaged {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
