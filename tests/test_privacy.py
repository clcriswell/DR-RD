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
    assert "Alice Smith" in redacted
    assert "Acme Corp" in redacted
    assert "[EMAIL_1]" in redacted
    assert "[PHONE_1]" in redacted

    pseudo, alias_map = pseudonymize_for_model(SAMPLE)
    assert alias_map == OrderedDict(
        [
            ("Alice Smith", "AliceSmithX1"),
            ("alice@acme.com", "[EMAIL_1]"),
            ("555-555-5555", "[PHONE_1]"),
            ("Bob Jones", "BobJonesX2"),
        ]
    )
    for token in alias_map.values():
        assert token in pseudo

    rehydrated = rehydrate_output(pseudo, alias_map)
    assert rehydrated == SAMPLE
