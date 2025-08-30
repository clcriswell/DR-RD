import os
from utils.runs import create_run_meta, list_runs
from utils.paths import ensure_run_dirs


def test_list_runs_newest_first(tmp_path):
    os.chdir(tmp_path)
    ids = [
        "1000000000-aa",  # older
        "1000000001-bb",
        "1000000002-cc",
    ]
    for rid in ids:
        ensure_run_dirs(rid)
        create_run_meta(rid, mode="m", idea_preview=f"idea {rid}")
    runs = list_runs()
    assert [r["run_id"] for r in runs[:3]] == ids[::-1]
    assert "idea" in runs[0]["idea_preview"]
