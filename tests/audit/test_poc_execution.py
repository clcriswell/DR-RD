def test_poc_execution_report_exists(audit_dir):
    assert (audit_dir / "4-poc-execution.md").exists()
