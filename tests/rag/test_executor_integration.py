from core import retrieval


def executor(task, plan):
    bundle = retrieval.run_retrieval(task["role"], task["task"], task["query"], plan, {})
    text = "\n".join(f"[{h.doc.meta['marker']}] {h.doc.text}" for h in bundle.hits)
    return {"content": text, "sources": bundle.sources}


def test_executor_adds_sources():
    plan = {"policy": "LIGHT", "top_k": 1}
    task = {"role": "Regulatory", "task": "t", "query": "regulation"}
    result = executor(task, plan)
    assert result["sources"]
    assert "[S1]" in result["content"]
