from pathlib import Path

from scripts.lint_docs import LINK_RE

REQUIRED = [
    "MIGRATION_GUIDE_v1_to_v2.md",
    "DEPRECATION_MAP.md",
    "VERSIONING_LTS.md",
    "COMPAT_MATRIX.md",
    "MAINTENANCE.md",
    "ROADMAP.md",
    "ONCALL_RUNBOOK.md",
    "ROLLBACK.md",
    "SUPPLY_CHAIN.md",
    "MODEL_ROUTING.md",
    "RAG_PIPELINE.md",
    "SAFETY_GOVERNANCE.md",
    "REPORTING.md",
    "EXAMPLE_BANK.md",
]


def test_docs_exist():
    docs = Path(__file__).resolve().parents[1] / "docs"
    for name in REQUIRED:
        assert (docs / name).is_file(), f"missing doc {name}"


def test_index_links_resolve():
    docs = Path(__file__).resolve().parents[1] / "docs"
    index = (docs / "INDEX.md").read_text(encoding="utf-8")
    for match in LINK_RE.finditer(index):
        link = match.group(1)
        if link.startswith("http"):
            continue
        target = (docs / link).resolve()
        assert target.exists(), f"broken link {link}"
