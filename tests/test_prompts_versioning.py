from utils.prompts import versioning


def test_bump_and_diff():
    assert versioning.next_version("1.2.3", "patch") == "1.2.4"
    assert versioning.next_version("1.2.3", "minor") == "1.3.0"
    assert versioning.is_upgrade("1.0.0", "1.0.1")
    diff = versioning.unified_diff("a\n", "b\n")
    assert "-a" in diff and "+b" in diff
