import json
import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from config.agent_models import AGENT_MODEL_MAP
from core.llm import complete
from core.plan_utils import normalize_plan_to_tasks, normalize_tasks
from core.router import choose_agent_for_task
from prompts.prompts import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT_TEMPLATE,
    SYNTHESIZER_TEMPLATE,
)
from core.observability import EvidenceSet, build_coverage
from utils.agent_json import extract_json_block
from memory.decision_log import log_decision
import csv
import os
import re

from core.agents_registry import agents_dict
import streamlit as st
from core.agents.planner_agent import PlannerAgent
from core.agents.registry import build_agents, load_mode_models
from core.synthesizer import synthesize
from utils.config import load_config
from utils.paths import new_run_dir
from utils.redaction import load_policy, redact_text
from core.dossier import Dossier, Finding


def _invoke_agent(agent, idea: str, task: Dict[str, str]) -> str:
    """Call an agent with best-effort interface detection."""
    text = f"{task.get('title','')}: {task.get('description','')}"
    # Preferred call signatures
    for name in ("run", "act", "execute", "__call__"):
        fn = getattr(agent, name, None)
        if callable(fn):
            try:
                return fn(idea, task)
            except TypeError:
                try:
                    return fn(text)
                except TypeError:
                    continue
    raise AttributeError(f"{agent.__class__.__name__} has no callable interface")


def generate_plan(
    idea: str,
    constraints: str | None = None,
    risk_posture: str | None = None,
) -> List[Dict[str, str]]:
    """Use the Planner to create and normalize a task list."""
    constraints_section = f"\nConstraints: {constraints}" if constraints else ""
    risk_section = f"\nRisk posture: {risk_posture}" if risk_posture else ""
    user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(
        idea=idea,
        constraints_section=constraints_section,
        risk_section=risk_section,
    )
    result = complete(PLANNER_SYSTEM_PROMPT, user_prompt)
    raw = result.content or ""
    tasks = normalize_tasks(normalize_plan_to_tasks(raw))
    return tasks


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:64] or "project"


def execute_plan(
    idea: str,
    tasks: List[Dict[str, str]],
    project_id: Optional[str] = None,
    save_decision_log: bool = True,
    save_evidence: bool = True,
    project_name: Optional[str] = None,
) -> Dict[str, str]:
    """Dispatch tasks to routed agents and collect their outputs."""
    project_id = project_id or _slugify(idea)
    project_name = project_name or project_id
    answers: Dict[str, str] = {}
    evidence = EvidenceSet(project_id=project_id) if save_evidence else None
    role_to_findings: Dict[str, dict] = {}
    for t in normalize_tasks(tasks):
        planned_role = t.get("role")
        title = t.get("title", "")
        description = t.get("description", "")
        role, AgentCls = choose_agent_for_task(planned_role, title, description)
        if save_decision_log:
            log_decision(project_id, "route", {"planned_role": planned_role, "title": title})
        model = AGENT_MODEL_MAP.get(role, AGENT_MODEL_MAP.get("Research Scientist", "gpt-5"))
        agent = AgentCls(model)
        try:
            out = _invoke_agent(agent, idea, {"title": title, "description": description})
        except Exception as e:
            out = f"ERROR: {e}"
        text = out if isinstance(out, str) else json.dumps(out)
        answers[role] = (answers.get(role, "") + ("\n\n" if role in answers else "") + text)
        payload = extract_json_block(text) or {}
        role_to_findings[role] = payload
        if evidence is not None:
            evidence.add(
                role=role,
                task_title=title,
                claim=payload.get("summary") or payload.get("findings", ""),
                sources=payload.get("sources", []),
                quotes=payload.get("quotes", []),
                tokens_in=payload.get("tokens_in", 0),
                tokens_out=payload.get("tokens_out", 0),
                cost_usd=payload.get("cost", 0.0),
            )
        if save_decision_log:
            log_decision(project_id, "agent_result", {"role": role, "has_json": bool(payload)})

    if save_evidence and evidence is not None:
        rows = build_coverage(project_id, role_to_findings)
        out_dir = os.path.join("audits", project_id)
        os.makedirs(out_dir, exist_ok=True)
        if rows:
            fieldnames = ["project_id", "role"] + [k for k in rows[0].keys() if k not in ("project_id", "role")]
            with open(os.path.join(out_dir, "coverage.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        with open(os.path.join(out_dir, "evidence.json"), "w", encoding="utf-8") as f:
            json.dump(evidence.as_dicts(), f, ensure_ascii=False, indent=2)
        if save_decision_log:
            log_decision(project_id, "coverage_built", {"rows": len(rows)})

    # Optional PoC stage
    try:
        import streamlit as st  # type: ignore

        enable_poc = st.session_state.get("enable_poc", False)
        test_plan = st.session_state.get("test_plan")
    except Exception:
        enable_poc = False
        test_plan = None
    if enable_poc and test_plan:
        report = run_poc(project_id, test_plan)
        try:
            st.session_state["poc_report"] = report
        except Exception:
            pass
    enable_build = os.environ.get("DRRD_ENABLE_BUILD_SPEC", "false").lower() == "true"
    if enable_build:
        from orchestrators.spec_builder import assemble_from_agent_payloads
        from utils.reportgen import render, write_csv

        sdd, impl = assemble_from_agent_payloads(project_name, idea, answers)
        out_dir = f"audits/{project_id}/build"
        os.makedirs(out_dir, exist_ok=True)
        sdd_md = render("build/SDD.md.j2", {"sdd": sdd})
        impl_md = render("build/ImplementationPlan.md.j2", {"impl": impl})
        open(f"{out_dir}/SDD.md", "w", encoding="utf-8").write(sdd_md)
        open(f"{out_dir}/ImplementationPlan.md", "w", encoding="utf-8").write(impl_md)
        write_csv(
            f"{out_dir}/bom.csv",
            [b.model_dump() for b in impl.bom],
            headers=["part_no", "desc", "qty", "unit_cost", "vendor"],
        )
        write_csv(
            f"{out_dir}/budget.csv",
            [b.model_dump() for b in impl.budget],
            headers=["phase", "cost_usd"],
        )
        os.makedirs(f"{out_dir}/interface_contracts", exist_ok=True)
        for i in sdd.interfaces:
            open(
                f"{out_dir}/interface_contracts/{i.name}.md",
                "w",
                encoding="utf-8",
            ).write(
                f"# {i.name}\n\nProducer: {i.producer}\nConsumer: {i.consumer}\n\nContract:\n{i.contract}\n"
            )

    return answers


def compile_proposal(idea: str, answers: Dict[str, str]) -> str:
    """Combine agent outputs into a final proposal using the Synthesizer."""
    findings_md = "\n".join(f"### {r}\n{a}" for r, a in answers.items())
    prompt = SYNTHESIZER_TEMPLATE.format(idea=idea, findings_md=findings_md)
    result = complete("You are an expert R&D writer.", prompt)
    return (result.content or "").strip()


def run_poc(project_id: str, test_plan):
    """Execute Proof-of-Concept tests defined in ``test_plan``."""
    from core.poc import gates
    from core.poc.testplan import TestPlan, TestCase, Metric
    from core.poc.results import TestResult, PoCReport
    from simulation import runner
    from simulation import simulation_manager  # ensure registry hooks
    from memory.memory_manager import MemoryManager
    from pathlib import Path
    import json
    import csv

    if not isinstance(test_plan, TestPlan):
        test_plan = TestPlan.parse_obj(test_plan)
    results = []
    total_cost = 0.0
    total_seconds = 0.0
    for test in test_plan.tests:
        gates.assert_safe(test)
        sim_name = test.inputs.get("_sim", "thermal_mock")
        obs, meta = runner.run_sim(sim_name, test.inputs)
        total_cost += float(meta.get("cost_estimate_usd", 0.0))
        total_seconds += float(meta.get("seconds", 0.0))
        metrics_passfail = {}
        for m in test.metrics:
            val = obs.get(m.name)
            passed = False
            if val is not None:
                if m.operator == ">=":
                    passed = val >= m.target
                elif m.operator == "<=":
                    passed = val <= m.target
                elif m.operator == ">":
                    passed = val > m.target
                elif m.operator == "<":
                    passed = val < m.target
                else:
                    passed = val == m.target
            metrics_passfail[m.name] = passed
        passed = all(metrics_passfail.values())
        results.append(
            TestResult(
                test_id=test.id,
                passed=passed,
                metrics_observed=obs,
                metrics_passfail=metrics_passfail,
                notes="",
            )
        )
        if test_plan.stop_on_fail and not passed:
            break
    summary = f"total_cost_usd={total_cost:.2f}, total_seconds={total_seconds:.2f}"
    report = PoCReport(
        project_id=test_plan.project_id,
        hypothesis=test_plan.hypothesis,
        results=results,
        summary=summary,
    )

    mm = MemoryManager()
    mm.attach_poc(project_id, test_plan.dict(), report.dict())

    out_dir = Path("audits") / project_id / "poc"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "testplan.json", "w", encoding="utf-8") as f:
        json.dump(test_plan.dict(), f, indent=2)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(report.dict(), f, indent=2)
    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["test_id", "passed", "metrics_observed", "metrics_passfail", "notes"]
        )
        writer.writeheader()
        for r in report.results:
            writer.writerow(r.dict())
    return report


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
    idea: str,
    mode: str = "test",
    *,
    session_id: str = "default",
    runs_dir: Path | None = None,
) -> Tuple[str, Dict[str, List[dict]], List[dict]]:
    """Run iterative planner → specialists → synthesis pipeline."""
    cfg = load_config()
    base_dir = runs_dir or Path(cfg.get("logging", {}).get("runs_dir", "runs"))
    run_dir = new_run_dir(base_dir)
    policy = {}
    if cfg.get("redaction", {}).get("enabled", True):
        policy = load_policy(cfg.get("redaction", {}).get("policy_file", "config/redaction.yaml"))
    dossier = Dossier(policy=policy)

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
            routed_role, AgentCls = choose_agent_for_task(
                task.get("role"), task.get("title", ""), task.get("description", "")
            )
            agent = agents.get(routed_role)
            if agent is None:
                base = agents.get("Research Scientist")
                model = getattr(base, "model", "gpt-5")
                agent = AgentCls(model)
                agents[routed_role] = agent
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
            dossier.record_finding(
                Finding(
                    id=f"{cycle}-{routed_role}",
                    title=task.get("title", ""),
                    body=summary_line,
                    evidences=[],
                    tags=[routed_role],
                )
            )
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
    dossier.save(run_dir / "dossier.json")
    return final, results_by_role, trace
