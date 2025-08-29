#!/usr/bin/env python3
import argparse
import zipfile
from pathlib import Path


DEF_TELE_DIR = Path('.dr_rd/telemetry')
DEF_PROV_DIR = Path('runs')


def main(out_path: str, telemetry_dir: Path, provenance_dir: Path) -> None:
    out = Path(out_path)
    with zipfile.ZipFile(out, 'w') as zf:
        for base in [telemetry_dir, provenance_dir]:
            if not base.exists():
                continue
            for p in base.rglob('*'):
                if p.is_file():
                    zf.write(p, p.relative_to(base.parent))
    print(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='support_bundle.zip')
    ap.add_argument('--telemetry-dir', default=str(DEF_TELE_DIR))
    ap.add_argument('--provenance-dir', default=str(DEF_PROV_DIR))
    args = ap.parse_args()
    main(args.out, Path(args.telemetry_dir), Path(args.provenance_dir))
