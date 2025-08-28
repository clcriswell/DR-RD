from dr_rd.prompting.prompt_factory import PromptFactory
from dr_rd.prompting import example_selectors
from dr_rd.examples import safety_filters


def test_prompt_factory_injects_examples(monkeypatch):
    monkeypatch.setattr(example_selectors, "score_candidates", lambda *a, **k: [
        {"input": "in1", "output": {"a": 1}},
        {"input": "in2", "output": {"a": 2}},
    ])
    monkeypatch.setattr(safety_filters, "filter_and_redact", lambda c, p: c)
    pf = PromptFactory()
    tpl = pf.registry.get("Planner")
    tpl.example_policy["max_tokens"] = 10
    prompt = pf.build_prompt({"role": "Planner", "inputs": {"task": "x"}})
    assert "few_shots" in prompt
    assert prompt["few_shots"]["summary"]["n"] == 1
    assert prompt["few_shots"]["provider"] == "openai"
