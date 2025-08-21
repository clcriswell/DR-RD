import json
import zipfile
import os
from core.final.composer import write_final_bundle, REQUIRED_SECTIONS


def test_write_final_bundle(tmp_path):
    # Prepare dummy appendix file
    appendix = tmp_path / "evidence.txt"
    appendix.write_text("data", encoding="utf-8")
    final_md = "# Title\n"
    # intentionally missing required sections
    cwd = tmp_path / "work"
    cwd.mkdir()
    os.chdir(cwd)
    out = write_final_bundle(
        "proj",
        final_md,
        {"evidence": str(appendix)},
        [],
    )
    report_text = (cwd / "audits" / "proj" / "final" / "final_report.md").read_text()
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in report_text
    with zipfile.ZipFile(out["bundle"], "r") as z:
        names = z.namelist()
    assert "final_report.md" in names
    assert "appendices_map.json" in names
    mapping = json.load(open(out["appendices_map"], "r", encoding="utf-8"))
    assert "evidence" in mapping
