import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    ["core.router", "core.agents.synthesizer_agent", "core.llm"],
)
def test_import_modules_no_nameerror(module):
    importlib.import_module(module)
