import json, os, logging
from core.agents.base_agent import BaseAgent
from core.llm import complete

log = logging.getLogger(__name__)

HRM_SYSTEM = """You are a Human R&D Manager. Given a project idea, enumerate the specialist roles required to execute the project end-to-end. 
Return ONLY JSON with shape:
{"roles": ["Role A", "Role B", "..."]}

Rules:
- Produce 6–14 roles.
- Prefer domain-specific titles over generic ones.
- Include cross-cutting roles only when critical (e.g., Regulatory, IP) but avoid repeating the same generic set every time.
- Example roles style: "Quantum Optics Physicist", "Nonlinear Optics / Crystal Engineer", "Photonics Electronics Engineer", "Software & Image-Processing Specialist", "AI R&D Coordinator", "Systems Integration & Validation Manager", "Electronics & Embedded Controls Engineer".
"""

HRM_USER_FMT = """Project Idea:
{idea}

Output strictly as JSON: {{"roles": [...]}}
"""

class HRMRoleAgent(BaseAgent):
    def __init__(self, **kwargs):
        model = kwargs.pop("model", os.getenv("DRRD_PLAN_MODEL", "gpt-4.1-mini"))
        super().__init__(name="HRM Role Agent", model=model, system_message="", user_prompt_template="", **kwargs)

    def discover_roles(self, idea: str) -> list[str]:
        user_prompt = HRM_USER_FMT.format(idea=idea)
        try:
            out = complete(HRM_SYSTEM, user_prompt, model=os.getenv("DRRD_PLAN_MODEL", "gpt-4.1-mini"))
        except TypeError:
            out = complete(HRM_SYSTEM, user_prompt)
        text = out if isinstance(out, str) else getattr(out, "content", str(out))
        try:
            data = json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            data = json.loads(text[start:end+1]) if start != -1 and end != -1 else {"roles": []}
        roles = data.get("roles", [])
        clean = []
        seen = set()
        for r in roles:
            rr = " ".join(str(r).split())
            if rr and rr.lower() not in seen:
                seen.add(rr.lower())
                clean.append(rr)
        log.info("HRM discovered roles: %s", clean)
        return clean
