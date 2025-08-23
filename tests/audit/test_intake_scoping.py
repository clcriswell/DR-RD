def test_intake_scoping_report_exists(audit_dir):
    assert (audit_dir / "0-intake-scoping.md").exists()
