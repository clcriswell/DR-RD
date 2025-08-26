from dr_rd.tools.code_io import summarize_diff, within_patch_limits
from dr_rd.tools.code_io import summarize_diff, within_patch_limits


def test_diff_summary_and_denylist():
    diff = """diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@\n+add\n-del\n"""
    summary = summarize_diff(diff)
    assert summary["changed_files"] == 1
    assert summary["additions"] == 1
    assert summary["deletions"] == 1
    assert summary["denied"] == []
    assert summary["ok"] == ["a.txt"]


def test_deny_and_caps():
    diff = """diff --git a/.git/config b/.git/config\n--- a/.git/config\n+++ b/.git/config\n@@\n+hi\n"""
    summary = summarize_diff(diff)
    assert ".git/config" in summary["denied"]
    multi = (
        "diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@\n+1\n"\
        "diff --git a/b.txt b/b.txt\n--- a/b.txt\n+++ b/b.txt\n@@\n+1\n"
    )
    assert not within_patch_limits(multi, max_files=1, max_bytes=1000)
    big = "diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@\n+" + ("x" * 50)
    assert not within_patch_limits(big, max_files=10, max_bytes=40)
