import json
import re
import logging
from typing import Dict, List, Tuple, Any

from core.agents_registry import agents_dict
import streamlit as st
from core.agents.planner_agent import PlannerAgent
from core.agents.registry import build_agents, choose_agent_for_task, load_mode_models
from core.synthesizer import synthesize
from core.plan_utils import normalize_plan_to_tasks, normalize_tasks


def orchestrate(user_idea: str) -> str:
    """Orchestrate the multi-agent R&D process for a given idea.

    This function expects a global ``agents_dict`` mapping role names to
    agent instances. Each agent must implement ``act(system_prompt, user_prompt)``.
    The function will coordinate the HR manager, planner, specialists, a
    reflection step, and finally the chief scientist who synthesizes results
    into a final plan.
    """

    global agents_dict

    print(f"[User] Idea submitted: {user_idea}")

    role_personas: Dict[str, str] = {
        "HRM": (
            "You are an HR Manager specializing in R&D projects. "
            "Identify the expert roles needed for the following idea."
        ),
        "Planner": (
            "You are a Project Planner AI. Decompose the given idea "
            "into specific tasks, noting the domain or role needed for each task."
        ),
        "Reflection": (
            "You are a Reflection agent analyzing the team's outputs. "
            "Determine if any additional follow-up tasks are required based on the results so far."
        ),
        "ChiefScientist": (
            "You are the Chief Scientist overseeing this project. "
            "Integrate all contributions into a comprehensive final R&D plan."
        ),
        "CTO": (
            "You are the Chief Technology Officer (CTO) for this project, focusing on technical strategy and feasibility. "
            "Address architecture, potential technical risks, and ensure coherence across domains in the plan."
        ),
        "ResearchScientist": (
            "You are a Research Scientist with expertise in the project's field. "
            "Research the state-of-the-art and summarize key findings, relevant studies, and gaps related to the idea."
        ),
        "MaterialsEngineer": (
            "You are a Materials Engineer specialized in material selection and engineering feasibility. "
            "Evaluate material and engineering aspects of the idea and suggest solutions to any challenges."
        ),
        "RegulatorySpecialist": (
            "You are a Regulatory Compliance Specialist. "
            "Review the idea for any regulatory or safety requirements and highlight compliance issues to address."
        ),
    }

    hrm_output = agents_dict["HRM"].act(role_personas["HRM"], user_idea)

    roles_needed: List[str] = []
    if isinstance(hrm_output, str):
        try:
            roles_needed = json.loads(hrm_output)
            if isinstance(roles_needed, dict):
                roles_needed = roles_needed.get("roles", list(roles_needed.values())[0] if roles_needed else [])
        except json.JSONDecodeError:
            parts = re.split(r"[\n,;]+", hrm_output)
            roles_needed = [role.strip() for role in parts if role.strip()]
    elif isinstance(hrm_output, (list, tuple)):
        roles_needed = list(hrm_output)
    else:
        try:
            roles_needed = list(hrm_output)
        except Exception:
            roles_needed = [str(hrm_output)]
    print(f"[HRM] Roles needed: {roles_needed}")

    planner_output = agents_dict["Planner"].act(role_personas["Planner"], user_idea)

    tasks: List[Dict[str, Any]] = []
    if isinstance(planner_output, str):
        try:
            plan_data = json.loads(planner_output)
        except json.JSONDecodeError:
            plan_data = {}
        if isinstance(plan_data, dict):
            tasks = plan_data.get("tasks", plan_data.get("Tasks", []))
        elif isinstance(plan_data, list):
            tasks = plan_data
    elif isinstance(planner_output, dict):
        tasks = planner_output.get("tasks") or planner_output.get("Tasks", []) or []
    elif isinstance(planner_output, list):
        tasks = planner_output

    normalized_tasks: List[Dict[str, Any]] = []
    for t in tasks:
        if isinstance(t, str):
            normalized_tasks.append({"task": t})
        elif isinstance(t, dict):
            task_desc = t.get("task") or t.get("Task") or ""
            domain = t.get("domain") or t.get("Domain") or None
            normalized_tasks.append({"task": task_desc, "domain": domain})
    tasks = normalized_tasks
    print(f"[Planner] Tasks identified: {tasks}")

    if not tasks:
        print("[Planner] No tasks were generated. Proceeding to final plan synthesis directly.")
        direct_input = f"Roles: {roles_needed}. Idea: {user_idea}. Provide a comprehensive R&D plan."
        final_plan = agents_dict["ChiefScientist"].act(role_personas["ChiefScientist"], direct_input)
        print("[ChiefScientist] Final plan (direct synthesis) ready.")
        return final_plan

    def assign_role(task: Dict[str, Any]) -> str:
        domain = task.get("domain")
        task_desc = task.get("task", "")
        if domain:
            dom_lower = str(domain).lower()
            for role_name in agents_dict.keys():
                if dom_lower in role_name.lower():
                    return role_name
            if "material" in dom_lower:
                return "MaterialsEngineer"
            if "regulator" in dom_lower or "compliance" in dom_lower:
                return "RegulatorySpecialist"
            if "science" in dom_lower or "research" in dom_lower:
                return "ResearchScientist"
            if "tech" in dom_lower or "engineer" in dom_lower:
                return "CTO"
        desc_lower = task_desc.lower()
        if any(word in desc_lower for word in ["material", "materials"]):
            return "MaterialsEngineer" if "MaterialsEngineer" in agents_dict else "MaterialsScientist"
        if any(word in desc_lower for word in ["regulatory", "regulation", "compliance"]):
            return "RegulatorySpecialist"
        if any(word in desc_lower for word in ["research", "analysis", "study"]):
            return "ResearchScientist"
        if any(word in desc_lower for word in ["technical", "architecture", "system design"]):
            return "CTO"
        if roles_needed:
            return roles_needed[0]
        return "ResearchScientist"

    all_outputs: Dict[str, List[Dict[str, Any]]] = {}
    for task in tasks:
        task_desc = task.get("task", "")
        role_assigned = assign_role(task)
        agent = agents_dict.get(role_assigned)
        if agent is None:
            print(f"[Warning] No agent found for role {role_assigned}, skipping task: {task_desc}")
            continue
        system_prompt = role_personas.get(role_assigned, f"You are a {role_assigned} expert.")
        user_prompt = task_desc
        result = agent.act(system_prompt, user_prompt)
        all_outputs.setdefault(role_assigned, []).append({"task": task_desc, "result": result})
        print(f"[{role_assigned}] Completed task: '{task_desc}' -> Result captured.")

    reflection_summary = ""
    for role, outputs in all_outputs.items():
        for entry in outputs:
            reflection_summary += f"\n- {role} on '{entry['task']}': {entry['result']}"
    reflection_user_prompt = (
        "The team of agents have completed their tasks with the following results:"
        f"{reflection_summary}\nGiven these results, determine if any additional follow-up tasks are needed to address remaining gaps or questions. "
        "If yes, list the new tasks (as a JSON list of task descriptions or task dicts with domains if applicable); if not, respond with 'no further tasks'."
    )
    reflection_output = agents_dict["Reflection"].act(role_personas["Reflection"], reflection_user_prompt)

    follow_up_tasks: List[Any] = []
    if reflection_output:
        if isinstance(reflection_output, str):
            if "no further tasks" in reflection_output.lower():
                follow_up_tasks = []
            else:
                try:
                    follow_up_tasks = json.loads(reflection_output)
                    if isinstance(follow_up_tasks, dict) and "tasks" in follow_up_tasks:
                        follow_up_tasks = follow_up_tasks["tasks"]
                    if isinstance(follow_up_tasks, dict):
                        follow_up_tasks = list(follow_up_tasks.values())
                except json.JSONDecodeError:
                    lines = [
                        line.strip("- ").strip()
                        for line in reflection_output.splitlines() if line.strip()
                    ]
                    if any("no further tasks" in line.lower() for line in lines):
                        follow_up_tasks = []
                    else:
                        for line in lines:
                            if line:
                                try:
                                    task_obj = json.loads(line)
                                    if isinstance(task_obj, str):
                                        follow_up_tasks.append({"task": task_obj})
                                    elif isinstance(task_obj, dict):
                                        follow_up_tasks.append(task_obj)
                                except json.JSONDecodeError:
                                    follow_up_tasks.append({"task": line})
        elif isinstance(reflection_output, list):
            follow_up_tasks = reflection_output
        elif isinstance(reflection_output, dict):
            follow_up_tasks = reflection_output.get("tasks") or list(reflection_output.values())

    if follow_up_tasks:
        print(f"[Reflection] Follow-up tasks suggested: {follow_up_tasks}")
        for ftask in follow_up_tasks:
            if isinstance(ftask, str):
                ftask = {"task": ftask}
            ftask_desc = ftask.get("task", "")
            role_assigned = assign_role(ftask)
            agent = agents_dict.get(role_assigned)
            if agent is None:
                print(f"[Warning] No agent for follow-up role {role_assigned}, skipping task: {ftask_desc}")
                continue
            system_prompt = role_personas.get(role_assigned, f"You are a {role_assigned} expert.")
            user_prompt = ftask_desc
            result = agent.act(system_prompt, user_prompt)
            all_outputs.setdefault(role_assigned, []).append({"task": ftask_desc, "result": result})
            print(f"[{role_assigned}] Completed follow-up task: '{ftask_desc}' -> Result captured.")
    else:
        print("[Reflection] No follow-up tasks needed.")

    synthesis_summary = ""
    for role, outputs in all_outputs.items():
        for entry in outputs:
            synthesis_summary += f"\n{role} ({entry['task']}): {entry['result']}"
    chief_user_prompt = (
        "All specialist tasks are complete. Here are the results:"
        f"{synthesis_summary}\nAs the Chief Scientist, please synthesize these contributions into a final comprehensive R&D plan."
    )
    final_plan = agents_dict["ChiefScientist"].act(role_personas["ChiefScientist"], chief_user_prompt)
    print("[ChiefScientist] Final R&D plan synthesized.")
    return final_plan


def run_pipeline(
    idea: str, mode: str = "test",
) -> Tuple[str, Dict[str, List[dict]], List[dict]]:
    """Run iterative planner → specialists → synthesis pipeline."""
    models = load_mode_models(mode)
    planner_model = models.get("Planner", models.get("default", "gpt-5"))
    planner = PlannerAgent(planner_model)
    agents = build_agents(mode, models=models)

    max_loops = int(st.session_state.get("MODE_CFG", {}).get("max_loops", 5))
    cycle = 0
    task_queue: List[dict] = []
    results_by_role: Dict[str, List[dict]] = {}
    trace: List[dict] = []
    context: Dict[str, List[str]] = {"idea": idea, "summaries": []}

    plan = planner.run(idea, "Decompose the project into specialist tasks")
    logger = logging.getLogger(__name__)
    logger.info(
        "Planner raw (first 400 chars): %s",
        str(getattr(planner, "last_raw", plan))[:400],
    )
    task_queue.extend(normalize_tasks(normalize_plan_to_tasks(plan)))

    while True:
        if not task_queue:
            followups = planner.revise_plan({"idea": idea, "results": results_by_role})
            if not followups:
                break
            task_queue.extend({"role": t.get("role"), "title": t.get("task")} for t in followups)
        cycle += 1
        batch = list(task_queue)
        task_queue.clear()
        for task in batch:
            routed_role, agent = choose_agent_for_task(
                task.get("role"), task.get("title", ""), agents
            )
            logger.info(
                "Dispatch '%s' planned_role=%s -> routed_role=%s",
                task.get("title"),
                task.get("role"),
                routed_role,
            )
            result = agent.act(idea, task.get("title", ""), context)
            results_by_role.setdefault(routed_role, []).append(result)
            summary_line = result.get("findings", [""])[0] if result.get("findings") else ""
            context["summaries"].append(summary_line)
            usage = result.get("usage", {})
            tokens = usage.get("total_tokens") or (
                usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            )
            trace.append({"agent": routed_role, "tokens": tokens, "finding": summary_line})
        logger.info(
            "Cycle %s — executed %s tasks; queue=%s", cycle, len(batch), len(task_queue)
        )
        if cycle >= max_loops and not task_queue:
            break

    final = synthesize(idea, results_by_role, model_id=models.get("synth", planner_model))
    return final, results_by_role, trace
