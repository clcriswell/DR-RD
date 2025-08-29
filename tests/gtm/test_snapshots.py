import tempfile
from pathlib import Path
from PIL import Image

from scripts.demos import flows


def test_snapshots_created():
    run_dir = Path(tempfile.mkdtemp())
    out_dir = Path(tempfile.mkdtemp())
    flows.run_all(run_dir)
    from scripts import snapshots

    snapshots.main(["--runs", str(run_dir), "--out", str(out_dir)])
    for name in snapshots.PRESETS:
        img = Image.open(out_dir / f"{name}.png")
        w, h = img.size
        assert w >= 800 and h >= 600
