from collections import OrderedDict

from core.privacy import (
    pseudonymize_for_model,
    rehydrate_output,
    redact_for_logging,
)


SAMPLE = (
    "Alice Smith from Acme Corp emailed alice@acme.com and called +1-555-555-5555. "
    "Bob Jones replied."
)


def test_redact_and_pseudonymization():
    redacted = redact_for_logging(SAMPLE)
    assert "[REDACTED:PERSON_1]" in redacted
    assert "[REDACTED:ORG_1]" in redacted
    assert "[REDACTED:EMAIL_1]" in redacted
    assert "[REDACTED:PHONE_1]" in redacted

    pseudo, alias_map = pseudonymize_for_model(SAMPLE)
    assert alias_map == OrderedDict(
        [
            ("Alice Smith", "[PERSON_1]"),
            ("Acme Corp", "[ORG_1]"),
            ("alice@acme.com", "[EMAIL_1]"),
            ("+1-555-555-5555", "[PHONE_1]"),
            ("Bob Jones", "[PERSON_2]"),
        ]
    )
    for token in alias_map.values():
        assert token in pseudo

    rehydrated = rehydrate_output(pseudo, alias_map)
    assert rehydrated == SAMPLE
