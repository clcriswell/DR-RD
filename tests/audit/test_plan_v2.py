def test_plan_v2_report_exists(audit_dir):
    assert (audit_dir / "3-plan-v2.md").exists()
