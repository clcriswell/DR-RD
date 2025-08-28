import pytest

from dr_rd.prompting import PromptRegistry, PromptTemplate, RetrievalPolicy


def test_register_get_list():
    registry = PromptRegistry()
    tpl = PromptTemplate(
        id="demo",
        version="v1",
        role="Demo",
        task_key=None,
        system="sys",
        user_template="user",
        io_schema_ref="schema.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    registry.register(tpl)
    assert registry.get("Demo") == tpl
    assert registry.list("Demo") == [tpl]
    assert registry.list() == [tpl]


def test_version_overwrite():
    registry = PromptRegistry()
    tpl1 = PromptTemplate(
        id="demo",
        version="v1",
        role="Demo",
        task_key=None,
        system="s1",
        user_template="u1",
        io_schema_ref="schema.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    tpl2 = PromptTemplate(
        id="demo",
        version="v2",
        role="Demo",
        task_key=None,
        system="s2",
        user_template="u2",
        io_schema_ref="schema.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    registry.register(tpl1)
    registry.register(tpl2)
    retrieved = registry.get("Demo")
    assert retrieved.version == "v2"
    assert retrieved.system == "s2"
