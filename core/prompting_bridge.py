"""Future bridge for prompt subsystem.

This module illustrates how an agent could request a prompt:

    from dr_rd.prompting import PromptFactory, registry
    factory = PromptFactory(registry)
    prompt = factory.build_prompt({"role": "Planner", "task": "<task>", "inputs": {"task": "<task>"}})

No runtime behavior change; not imported elsewhere yet.
"""
