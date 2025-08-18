import logging
from core.agents.unified_registry import build_agents_unified, ensure_canonical_agent_keys, choose_agent_for_task
from core.plan_utils import normalize_plan_to_tasks, normalize_tasks
from core.roles import canonical_roles

logger = logging.getLogger(__name__)


def get_agents():
    agents = build_agents_unified()
    agents = ensure_canonical_agent_keys(agents)
    logger.info("Registered agents (unified): %s", sorted(agents.keys()))
    return agents

FALLBACK_ORDER = ["Research Scientist","Research","AI R&D Coordinator","Mechanical Systems Lead"]

def _pick_default_agent(agents: dict):
    for k in FALLBACK_ORDER:
        if k in agents:
            return k, agents[k]
    k = next(iter(agents.keys()))
    return k, agents[k]


def route_tasks(tasks_any, agents):
    agents = ensure_canonical_agent_keys(agents)
    tasks = normalize_tasks(normalize_plan_to_tasks(tasks_any))
    routed = []
    for t in tasks:
        role = t["role"]; title = t["title"]; desc = t["description"]
        try:
            rr, agent = choose_agent_for_task(role, title, desc, agents)
        except TypeError:
            agent, rr = choose_agent_for_task(role, title, agents)
        if not agent:
            low = (title + " " + desc).lower()
            agent = agents.get("Marketing Analyst") if "market" in low else None
            rr = "Marketing Analyst" if agent else role
        if not agent:
            rr, agent = _pick_default_agent(agents)
        routed.append((rr, agent, t))
    return routed


def classic_execute(tasks, idea, agents):
    outputs = {}
    routed = route_tasks(tasks, agents)
    logger.info("Planner routing: %s", [{"from": t["role"], "to": rr} for rr, _, t in routed])
    logger.info("Final routed task count: %d", len(routed))

    for rr, agent, t in routed:
        try:
            out = agent.run(idea, {"role": rr, "title": t["title"], "description": t["description"]})
        except Exception as e:
            logger.exception("Agent %s failed: %s", rr, e)
            out = {"error": str(e)}
        outputs.setdefault(rr, []).append({
            "title": t["title"],
            "description": t["description"],
            "output": out,
        })
    return outputs
