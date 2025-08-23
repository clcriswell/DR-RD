import json

from utils.redaction import load_policy

from core.dossier import Dossier, Evidence, Finding


def test_record_and_save_with_redaction(tmp_path):
    policy = load_policy("config/redaction.yaml")
    d = Dossier(policy=policy)
    f = Finding(
        id="1",
        title="Email john.doe@example.com",
        body="Call 555-123-4567",
        evidences=[Evidence(source_id="s", uri="u", snippet="john.doe@example.com")],
    )
    d.record_finding(f)
    path = tmp_path / "dossier.json"
    d.save(path)
    data = json.loads(path.read_text())
    snippet = data["findings"][0]["evidences"][0]["snippet"]
    assert "[REDACTED:EMAIL]" in snippet
    assert "[REDACTED:PHONE]" in data["findings"][0]["body"]
