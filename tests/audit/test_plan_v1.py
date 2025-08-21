
def test_plan_v1_report_exists(audit_dir):
    assert (audit_dir / "1-plan-v1.md").exists()
