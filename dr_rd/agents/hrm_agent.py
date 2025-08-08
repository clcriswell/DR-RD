class HRMAgent:
    """
    Wraps an underlying agent with:
      - multi-candidate generation (top_k)
      - simple evaluator scoring (avg)
      - one retry if below threshold
      - ws.log of chosen variant & retries
    """

    def __init__(self, agent, evaluators, ws, name, top_k=3, max_retries=1, threshold=0.75):
        self.agent, self.evaluators, self.ws, self.name = agent, evaluators, ws, name
        self.top_k, self.max_retries, self.threshold = top_k, max_retries, threshold

    def run(self, *args, context=None, **kwargs):
        cands = []
        for i in range(self.top_k):
            try:
                cands.append(self.agent.run(*args, context=context, variant=i, **kwargs))
            except TypeError:
                cands.append(self.agent.run(*args, **kwargs))
        best, score, idx = self._pick_best(cands, context)
        tries = 0
        while score < self.threshold and tries < self.max_retries:
            try:
                refined = self.agent.run(*args, context=context, **kwargs)
            except TypeError:
                refined = self.agent.run(*args, **kwargs)
            best, score, idx = self._pick_best([best, refined], context)
            tries += 1
        self.ws.log(f"HRM.Agent[{self.name}] picked variant {idx+1}, score={score:.2f} (retry={tries})")
        return best

    def _pick_best(self, outputs, ctx):
        scs = [self._score(o, ctx) for o in outputs]
        i = max(range(len(scs)), key=lambda k: scs[k])
        return outputs[i], scs[i], i

    def _score(self, output, ctx):
        vals = []
        for ev in self.evaluators:
            try:
                vals.append(float(ev(output, ctx)))
            except Exception:
                vals.append(0.0)
        return sum(vals) / len(vals) if vals else 0.0

    def revise_plan(self, *args, **kwargs):
        if hasattr(self.agent, "revise_plan"):
            return self.agent.revise_plan(*args, **kwargs)
        raise AttributeError("Underlying agent lacks revise_plan")
