from dr_rd.compliance import checker


def test_compliance_coverage():
    profile = checker.load_profile("us_federal")
    text = "We follow FDA guidelines and OSHA safety rules."
    report = checker.check(text, profile, {})
    assert report.coverage > 0
    assert "us4" in report.unmet  # hipaa not mentioned
