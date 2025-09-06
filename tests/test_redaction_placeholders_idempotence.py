from core.redaction import Redactor

def test_placeholders_and_idempotence():
    r = Redactor()
    t1, am, ph = r.redact("Contact John Doe at 192.168.0.1", mode="light", role=None)
    assert t1 == "Contact JohnDoeX1 at [IP_1]"
    t2, am2, ph2 = r.redact(t1, mode="light", role=None)
    assert t2 == t1  # idempotent
