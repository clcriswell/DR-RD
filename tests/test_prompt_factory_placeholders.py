import json
import pytest

from dr_rd.prompting.prompt_factory import PromptFactory
from dr_rd.prompting.prompt_registry import PromptRegistry, PromptTemplate, RetrievalPolicy


def _make_factory(template):
    reg = PromptRegistry()
    reg.register(template)
    return PromptFactory(registry=reg)


def test_missing_placeholder():
    tpl = PromptTemplate(
        id="t",
        version="v1",
        role="R",
        task_key=None,
        system="s",
        user_template="Hello {{ name }}!",
        io_schema_ref="",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    factory = _make_factory(tpl)
    with pytest.raises(ValueError) as e:
        factory.build_prompt({"role": "R", "inputs": {}})
    assert "name" in str(e.value)


def test_placeholder_render():
    tpl = PromptTemplate(
        id="t",
        version="v1",
        role="R",
        task_key=None,
        system="s",
        user_template="Hello {{ name }}!",
        io_schema_ref="",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    factory = _make_factory(tpl)
    prompt = factory.build_prompt({"role": "R", "inputs": {"name": "Ada"}})
    assert prompt["user"] == "Hello Ada!"
