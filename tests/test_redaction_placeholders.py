from core.redaction import Redactor
from core.redaction import Redactor
from core.privacy import redact_for_logging
from dr_rd.prompting.prompt_factory import PromptFactory


def test_replacement_and_idempotence():
    r = Redactor()
    out, _, _ = r.redact("Contact John at 192.168.0.1")
    assert out == "Contact JohnX1 at [IP_1]"
    out2, _, _ = r.redact(out)
    assert out2 == out


def test_whitelist():
    r = Redactor(global_whitelist={"PERSON": {"John"}})
    out, _, _ = r.redact("John met Bob Jones")
    assert "John" in out
    assert "BobJonesX1" in out


def test_modes():
    r = Redactor()
    light, _, _ = r.redact("John Doe at Acme Inc, 1 Main St", mode="light")
    assert "JohnDoeX1" in light
    assert "Acme Inc" in light
    assert "1 Main St" in light
    r2 = Redactor()
    heavy, _, _ = r2.redact("John Doe at Acme Inc, 1 Main St", mode="heavy")
    assert "[PERSON_1]" in heavy
    assert "[ORG_1]" in heavy
    assert "[ADDRESS_1]" in heavy


def test_integration_prompt_and_logging():
    pf = PromptFactory()
    prompt = pf.build_prompt({"role": "Tester", "task": "Review [PERSON_1] case"})
    assert "aliases" in prompt["system"]
    red = redact_for_logging("John from Acme Inc")
    assert red == "John from Acme Inc"
