import random
import re

from core.redaction import Redactor
from core.privacy import redact_for_logging, pseudonymize_for_model, rehydrate_output


def test_roles_preserved_and_pii_redacted():
    text = "CTO Jane Doe <jane@example.com>"
    red = redact_for_logging(text)
    assert "CTO" in red
    assert "example.com" not in red


def test_pseudonymize_roundtrip():
    payload = {"name": "Jane Doe", "email": "jane@example.com"}
    pseudo, mapping = pseudonymize_for_model(payload)
    assert pseudo["name"] != payload["name"]
    assert "example.com" not in str(pseudo)
    restored = rehydrate_output(pseudo, mapping)
    assert restored == payload


def test_project_alias_normalization_and_rehydration(monkeypatch):
    r = Redactor()
    r.project_name = "A Quantum Entanglement Microscope Device"
    monkeypatch.setattr(random, "choice", lambda seq: "System")
    redacted, alias_map, _ = r.redact(
        "Discussion on A Quantum Entanglement Microscope Device", role="CTO"
    )
    alias = alias_map["A Quantum Entanglement Microscope Device"]
    assert not re.match(r"^(A|An|The)", alias)
    assert not alias.endswith("DeviceSystem")
    output = f"The {alias} performed well."
    restored = rehydrate_output(output, alias_map)
    assert "A Quantum Entanglement Microscope Device" in restored
    assert alias not in restored
