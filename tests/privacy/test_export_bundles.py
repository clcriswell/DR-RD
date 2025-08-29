from pathlib import Path
import zipfile
import yaml

from dr_rd.privacy import export, subject

CFG = yaml.safe_load(open("config/retention.yaml"))


def test_export_bundles(monkeypatch):
    tenant = ("org2", "ws2")
    root = Path.home() / ".dr_rd" / "tenants" / "org2" / "ws2" / "kb"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PRIVACY_SALT", "salt")
    key = subject.derive_subject_key({"email": "b@example.com"}, ["email"], "PRIVACY_SALT")
    f = root / "file.txt"
    f.write_text(key)
    tenant_zip = export.export_tenant(tenant)
    assert Path(tenant_zip).exists()
    with zipfile.ZipFile(tenant_zip) as z:
        assert "manifest.json" in z.namelist()
    subj_zip = export.export_subject(tenant, key)
    with zipfile.ZipFile(subj_zip) as z:
        names = z.namelist()
        assert any(name.endswith("file.txt") for name in names)
        assert "manifest.json" in names
