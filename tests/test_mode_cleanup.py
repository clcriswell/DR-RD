from __future__ import annotations

import pathlib

import pytest

from dr_rd.config.loader import load_config

DEPRECATED_TERMS = [
    "TEST_MODE",
    "DRRD_MODE",
    "deep mode",
    "DISABLE_IMAGES_BY_DEFAULT",
    "DRRD_SUPERUSER_MODE",
]


def test_load_config_rejects_non_standard_profile():
    with pytest.raises(ValueError):
        load_config("defaults", profile="legacy")


def test_no_deprecated_mode_terms():
    root = pathlib.Path(__file__).resolve().parents[1]
    bases = [root / "dr_rd", root / "scripts"]
    for base in bases:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                for term in DEPRECATED_TERMS:
                    assert term not in text, f"{term} found in {path}"
