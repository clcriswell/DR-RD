def test_research_execution_report_exists(audit_dir):
    assert (audit_dir / "2-research-execution.md").exists()
