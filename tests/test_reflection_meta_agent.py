from dr_rd.agents.reflector import ReflectorMetaAgent


def test_reflector_switches_strategy_on_stagnation():
    history = [
        {"cycle": 0, "score": 0.5, "sim_failures": 0},
        {"cycle": 1, "score": 0.5, "sim_failures": 0},
    ]
    agent = ReflectorMetaAgent()
    adjustments = agent.reflect(history)
    assert adjustments.get("switch_to_tot")
    assert adjustments.get("new_tasks")
