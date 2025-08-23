def test_plan_v3_report_exists(audit_dir):
    assert (audit_dir / "5-plan-v3.md").exists()
