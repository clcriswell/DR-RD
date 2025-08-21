from pathlib import Path
import pytest

AUDIT_DATE = "2025-08-21"

@pytest.fixture
def audit_dir():
    """Path to today's audit reports."""
    return Path("audits") / AUDIT_DATE
