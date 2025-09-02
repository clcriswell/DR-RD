from orchestrators.executor import execute
from utils.paths import artifact_path


def test_executor_creates_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = [{"title": "Do thing"}]
    ctx = {"run_id": "r1", "idea": "Idea"}
    paths = execute(plan, ctx)
    spec = artifact_path("r1", "build_spec", "md")
    plan_p = artifact_path("r1", "work_plan", "md")
    assert spec.exists()
    assert plan_p.exists()
    assert paths["build_spec"] == spec
    assert paths["work_plan"] == plan_p
