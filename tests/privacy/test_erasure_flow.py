from pathlib import Path
import yaml

from dr_rd.privacy import subject, erasure
from core import audit_log, provenance

CFG = yaml.safe_load(open("config/retention.yaml"))


def test_erasure_flow(monkeypatch):
    tenant = ("org", "ws")
    root = Path.home() / ".dr_rd" / "tenants" / "org" / "ws" / "kb"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PRIVACY_SALT", "s1")
    key = subject.derive_subject_key({"email": "a@example.com"}, ["email"], "PRIVACY_SALT")
    f = root / "file.txt"
    f.write_text(key)
    erasure.mark_subject_for_erasure(tenant, key, "test", "tester")
    impact = erasure.preview_impact(tenant, key)
    assert str(f) in impact
    erasure.execute_erasure(tenant, key, CFG)
    assert key not in f.read_text()
    receipts = Path.home() / ".dr_rd" / "tenants" / "org" / "ws" / "privacy" / "receipts"
    assert any(p.name.startswith("execute") for p in receipts.iterdir())
    audit_path = Path.home() / ".dr_rd" / "tenants" / "org" / "ws" / "audit" / "audit.jsonl"
    assert "REDACTION" in audit_path.read_text()
    prov_path = Path("runs") / provenance.RUN_ID / "provenance_redactions.jsonl"
    assert prov_path.exists() and "REDACTION" in prov_path.read_text()
