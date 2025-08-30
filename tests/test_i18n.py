from utils.i18n import tr, missing_keys


def test_fallback_to_english():
    # run_help only defined in en.json
    assert tr("run_help", lang="es") == "The app plans tasks, executes, and synthesizes a report."


def test_formatting_substitution():
    assert tr("greet", name="Alex") == "Hello Alex"


def test_missing_keys():
    miss = missing_keys("es")
    assert "run_help" in miss
