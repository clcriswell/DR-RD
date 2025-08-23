import logging

from core.llm_client import call_openai
from core.model_router import CallHints, pick_model


def refine_agent_output(agent, idea, task, prev_output, other_outputs):
    """
    Refine an agent's output given its previous output and other agents' outputs.
    """
    # Compile other agents' outputs into context text
    others_context = ""
    if other_outputs:
        for role, text in other_outputs.items():
            others_context += f"\n{role} output:\n{text}\n"
    user_prompt = (
        f"Project Idea: {idea}\n"
        f"Role: {agent.name}\n"
        f"Task: {task}\n\n"
        f"Previous {agent.name} output:\n{prev_output}\n\n"
        f"Other team members' outputs:{others_context}\n"
        "Please refine and improve your output given the above information, addressing any gaps or integrating relevant insights from the others."
    )
    sel = pick_model(CallHints(stage="exec"))
    logging.info(f"Model[exec]={sel['model']} params={sel['params']}")
    result = call_openai(
        model=sel["model"],
        messages=[
            {"role": "system", "content": agent.system_message},
            {"role": "user", "content": user_prompt},
        ],
        **sel["params"],
    )
    return (result["text"] or "").strip()
