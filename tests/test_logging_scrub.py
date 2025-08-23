import logging

from utils.logging import safe_exc


def test_safe_exc_scrubs(caplog):
    with caplog.at_level(logging.ERROR, logger="drrd"):
        safe_exc(
            None,
            "Build ACME SuperBattery 3000",
            "boom",
            Exception("ceo@acme.com https://x.y"),
        )
    out = caplog.text
    assert "ceo@acme.com" not in out
    assert "https://x.y" not in out
    assert "SuperBattery" not in out
