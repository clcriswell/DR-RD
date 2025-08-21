from core.llm import complete


def test_dry_run(monkeypatch):
    monkeypatch.setenv("DRRD_DRY_RUN", "true")
    res = complete("system", "hello")
    assert res.content.startswith("[DRY_RUN]")
