import logging

import config.model_routing as mr


def test_mode_argument_deprecated(caplog):
    with caplog.at_level(logging.WARNING):
        model_test = mr.pick_model(stage="plan", role=None, mode="test")
        model_deep = mr.pick_model(stage="plan", role=None, mode="deep")
        model_stage = mr.pick_model_for_stage("plan")

    assert model_test == model_deep == model_stage
    warnings = [r for r in caplog.records if "mode' argument is deprecated" in r.message]
    assert len(warnings) == 2
