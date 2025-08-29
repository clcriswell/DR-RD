import subprocess
import sys
import zipfile
from pathlib import Path


def test_collect_support_bundle(tmp_path):
    tele = tmp_path / "tele"
    prov = tmp_path / "prov"
    tele.mkdir()
    prov.mkdir()
    (tele / "t.jsonl").write_text("{}")
    (prov / "p.jsonl").write_text("{}")
    out = tmp_path / "bundle.zip"
    script = Path("scripts/collect_support_bundle.py")
    subprocess.check_call(
        [
            sys.executable,
            str(script),
            "--out",
            str(out),
            "--telemetry-dir",
            str(tele),
            "--provenance-dir",
            str(prov),
        ]
    )
    with zipfile.ZipFile(out, "r") as zf:
        names = zf.namelist()
        assert any("t.jsonl" in n for n in names)
        assert any("p.jsonl" in n for n in names)
