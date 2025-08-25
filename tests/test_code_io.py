from dr_rd.tools import read_repo, plan_patch, apply_patch


def test_read_repo_no_matches():
    assert read_repo(["nonexistent/**/*.py"]) == []


def test_plan_patch_passthrough():
    diff = "sample diff"
    assert plan_patch(diff) == diff


def test_apply_patch_dry_run():
    diff = """\
diff --git a/tmp.txt b/tmp.txt
new file mode 100644
--- /dev/null
+++ b/tmp.txt
@@
+hello
"""
    res = apply_patch(diff, dry_run=True)
    assert res["status"] == "validated"
