import logging
from core.model_router import pick_model, CallHints
from core.llm_client import call_openai

def agent_chat(agentA, agentB, idea, outputA, outputB):
    """
    Let agentA and agentB (e.g. CTO and Research Scientist) discuss the idea and their outputs.
    Returns a tuple of (updated_output_A, updated_output_B) after clarification.
    """
    prompt = (
        f"Project Idea: {idea}\n\n"
        f"{agentA.name} initial output:\n{outputA}\n\n"
        f"{agentB.name} initial output:\n{outputB}\n\n"
        "The CTO will ask the Research Scientist one clarification question about the Research Scientist's findings, and the Research Scientist will answer it. "
        "Then the Research Scientist will ask the CTO one question about the CTO's analysis, and the CTO will answer it. "
        "After this exchange, update both the CTO's and the Research Scientist's outputs with any new insights. "
        "Provide only the final revised outputs, labeled as 'CTO Updated Output:' and 'Research Scientist Updated Output:'."
    )
    sel = pick_model(CallHints(stage="exec"))
    logging.info(f"Model[exec]={sel['model']} params={sel['params']}")
    result = call_openai(
        model=sel["model"],
        messages=[{"role": "user", "content": prompt}],
        **sel["params"],
    )
    content = (result["text"] or "").strip()
    # Extract updated outputs from the response content
    updated_cto = ""
    updated_rs = ""
    if "CTO Updated Output:" in content:
        parts = content.split("Research Scientist Updated Output:")
        if len(parts) == 2:
            cto_part, rs_part = parts
            idx = cto_part.find("CTO Updated Output:")
            if idx != -1:
                updated_cto = cto_part[idx + len("CTO Updated Output:"):].strip()
            else:
                updated_cto = cto_part.strip()
            updated_rs = rs_part.strip()
        else:
            updated_cto = content.strip()
            updated_rs = ""
    else:
        # Fallback: split content roughly in half if labels not found
        lines = content.splitlines()
        mid = len(lines) // 2
        updated_cto = "\n".join(lines[:mid]).strip()
        updated_rs = "\n".join(lines[mid:]).strip()
    return updated_cto, updated_rs
