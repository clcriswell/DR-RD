from evaluators import redteam_jailbreak


def test_jailbreaks_pass():
    assert redteam_jailbreak.run_harness()
