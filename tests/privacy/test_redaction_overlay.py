from pathlib import Path
import json

from core import redaction_overlay


def test_overlay(tmp_path):
    base = tmp_path / "audit.jsonl"
    red = tmp_path / "redactions.jsonl"
    entry = {"hash": "abc", "msg": "hello"}
    base.write_text(json.dumps(entry) + "\n")
    r = {"target_hash": "abc", "event": "REDACTION", "reason": "ERASURE_REQUEST", "redaction_token": "[R]"}
    red.write_text(json.dumps(r) + "\n")
    merged = redaction_overlay.merge_logs(base, red)
    assert merged[0]["redacted"] is True
    assert merged[0]["redaction_token"] == "[R]"
