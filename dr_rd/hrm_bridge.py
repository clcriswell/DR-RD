class HRMBridge:
    def __init__(self, loop_cls, ws):
        self.loop_cls, self.ws = loop_cls, ws

    def plan_only(self, brief, replan=False):
        tasks = self.loop_cls.plan_from_brief(brief)
        try:
            n = len(tasks) if hasattr(tasks, "__len__") else 0
        except Exception:
            n = 0
        tag = "HRM.Replan" if replan else "HRM.Plan"
        self.ws.log(f"{tag} → {n} tasks")
        return tasks

    def evaluate_only(self, results):
        ev = self.loop_cls.evaluate_results(results) or {}
        score = float(ev.get("score", 0.0))
        notes = ev.get("notes", [])
        cov = float(ev.get("coverage_confidence", 0.0))
        self.ws.log(f"HRM.Eval → score={score:.2f}, cov={cov:.2f}")
        return score, notes, cov

    def seek_help_only(self, brief, results=None):
        advice = self.loop_cls.get_help(brief=brief, context=results) or []
        used = 1 if advice else 0
        self.ws.log(f"HRM.Help → used={used}")
        return advice
