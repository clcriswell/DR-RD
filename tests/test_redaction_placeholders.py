from core.redaction import Redactor
from core.privacy import redact_for_logging
from dr_rd.prompting.prompt_factory import PromptFactory


def test_replacement_and_idempotence():
    r = Redactor()
    out, _, _ = r.redact("Contact John at 192.168.0.1")
    assert out == "Contact [PERSON_1] at [IP_1]"
    out2, _, _ = r.redact(out)
    assert out2 == out


def test_whitelist():
    r = Redactor(global_whitelist={"PERSON": {"John"}})
    out, _, _ = r.redact("John met Bob")
    assert "John" in out
    assert "[PERSON_1]" in out


def test_modes():
    r = Redactor()
    light, _, _ = r.redact("John at Acme Inc, 1 Main St", mode="light")
    assert "[PERSON_1]" in light
    assert "Acme Inc" in light
    assert "1 Main St" in light
    heavy, _, _ = r.redact("John at Acme Inc, 1 Main St", mode="heavy")
    assert "[ORG_1]" in heavy
    assert "[ADDRESS_1]" in heavy


def test_integration_prompt_and_logging():
    pf = PromptFactory()
    prompt = pf.build_prompt({"role": "Tester", "task": "Review [PERSON_1] case"})
    assert "Placeholders like [PERSON_1], [ORG_1] are aliases." in prompt["system"]
    red = redact_for_logging("John from Acme Inc")
    assert "[PERSON_1]" in red and "[ORG_1]" in red
