from agents.base_agent import BaseAgent
import logging
import openai

"""Planner Agent for developing project plans."""
class PlannerAgent(BaseAgent):
    """Agent that creates a detailed project plan for the given idea."""

    def __init__(self, model):
        super().__init__(
            name="Planner",
            model=model,
            system_message=(
                "You are an expert project planner specializing in turning ideas into actionable plans."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\n"
                "As the Planner, your task is {task}.\n\n"
                "Return **only** a JSON object mapping each relevant team role (from the list below) to one or two succinct tasks. "
                "Include a role only if it would reasonably contribute to this project:\n"
                "  - Mechanical Systems Lead\n"
                "  - Materials & Process Engineer\n"
                "  - Chemical & Surface Science Specialist\n"
                "  - Quantum Optics Physicist\n"
                "  - Nonlinear Optics / Crystal Engineer\n"
                "  - Optical Systems Engineer\n"
                "  - Mechanical & Precision-Motion Engineer\n"
                "  - Photonics Electronics Engineer\n"
                "  - Electronics & Embedded Controls Engineer\n"
                "  - Software / Image-Processing Specialist\n"
                "  - Fluorescence / Biological Sample Expert\n"
                "  - Systems Integration & Validation Engineer\n"
                "  - Data Scientist / Analytics Engineer\n"
                "  - Regulatory & Compliance Lead\n"
                "  - Prototyping & Test Lab Manager\n"
                "  - Project Manager / Principal Investigator\n"
                "  - Product Manager / Translational Lead\n"
                "  - AI R&D Coordinator\n\n"
                "Only include roles that are relevant, and do not include any roles outside this list. "
                "Use each role name exactly as given above as JSON keys, and provide a brief task description for each selected role."
            ),
        )

    def run(self, idea: str, task: str) -> dict:
        """Return the planner's JSON summary as a Python dict."""
        import json

        prompt = self.user_prompt_template.format(idea=idea, task=task)

        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
        }

        # Only newer models (e.g. gpt-4o, gpt-4.1) support the
        # `response_format` parameter for structured JSON output. Older
        # completion models will raise a 400 error if it is supplied. To keep
        # compatibility with both we add the parameter conditionally.
        if self.model.startswith(("gpt-4o", "gpt-4.1")):
            kwargs["response_format"] = {"type": "json_object"}

        response = openai.chat.completions.create(**kwargs)
        raw_text = response.choices[0].message.content
        logging.debug("Planner raw response: %s", raw_text)
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Planner returned invalid JSON: {raw_text}") from e

    def revise_plan(self, workspace_state: dict) -> list[dict]:
        """
        Given the full workspace state (tasks, results, scores),
        produce an updated list of tasks (may add, remove, reorder).
        Returns a list of dicts: [{ "role": str, "task": str, "id": str }, ...].
        """
        import json, hashlib, time
        # Build prompt
        sys = (
            "You are the R&D meta‐planner. "
            "Given the workspace state below, revise the list of tasks: "
            "- Add missing high‐level tasks, "
            "- Drop completed or irrelevant tasks, "
            "- Reorder for priority.\n"
            "Respond with JSON: { \"updated_tasks\": [ { \"role\": \"...\", \"task\": \"...\" } , ... ] }"
        )
        user = json.dumps(workspace_state, indent=2)[:8000]
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[{"role":"system","content":sys},
                      {"role":"user","content":user}]
        )
        try:
            data = resp.choices[0].message.content
            parsed = json.loads(data)
            out = []
            for t in parsed.get("updated_tasks", []):
                tid = hashlib.sha1((t["role"]+t["task"]+str(time.time())).encode()).hexdigest()[:10]
                out.append({"role": t["role"], "task": t["task"], "id": tid})
            return out
        except Exception:
            # fallback: return existing queue unchanged
            return workspace_state.get("tasks", [])
