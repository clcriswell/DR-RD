import json
from pathlib import Path
import tempfile

from scripts.demos import flows


def _run(flow_name: str) -> Path:
    td = tempfile.mkdtemp()
    out = Path(td)
    if flow_name == "all":
        flows.run_all(out, flags="ENABLE_LIVE_SEARCH=0")
    else:
        flows.FLOW_MAP[flow_name](out, flags="ENABLE_LIVE_SEARCH=0")
    return out


def test_materials_flow():
    out = _run("materials")
    assert (out / "materials.json").exists()


def test_compliance_sources():
    out = _run("compliance")
    data = json.loads((out / "compliance.json").read_text())
    assert data["items"][0]["sources"]
