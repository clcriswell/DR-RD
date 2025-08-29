from scripts.stale_code_scan import scan


def test_reports_orphan_module(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    orphan = pkg / "orphan.py"
    orphan.write_text("x = 1\n")
    repo_map = tmp_path / "repo_map.yaml"
    repo_map.write_text("modules: []\n")
    result = scan([pkg], str(repo_map), tmp_path)
    assert "pkg/orphan.py" in result["orphan_files"]
