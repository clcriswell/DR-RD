import core.retrieval.query_builder as qb


def test_query_builder_uniqueness_and_bounds():
    task = "study study longword" * 2
    idea = "improve research"
    constraints = ["cost", "speed", "speed"]
    queries = qb.build_queries(task, idea, constraints, "low")
    assert len(queries) == len(set(queries))
    assert all(len(q) <= qb.MAX_QUERY_LEN for q in queries)
    assert len(queries) <= qb.MAX_QUERIES_PER_TASK
