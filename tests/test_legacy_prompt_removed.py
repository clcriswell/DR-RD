from pathlib import Path

from dr_rd.prompting import registry


def test_synthesizer_prompt_no_legacy_headings():
    tpl = registry.get("Synthesizer")
    assert tpl is not None
    legacy_headings = ["## Regulatory & Compliance", "## IP & Prior Art"]
    for heading in legacy_headings:
        assert heading not in tpl.user_template


def test_no_legacy_strings_in_dr_rd():
    root = Path(__file__).resolve().parents[1] / "dr_rd"
    legacy_headings = ["## Regulatory & Compliance", "## IP & Prior Art"]
    for path in root.rglob("*"):
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for heading in legacy_headings:
                assert heading not in text, f"{heading} found in {path}"
