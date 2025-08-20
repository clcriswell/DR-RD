import os, tempfile, textwrap
from core.agents.qa_agent import syntax_check, detect_imports, patch_requirements, write_smoke_test

def test_syntax_and_imports_minimal():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "pages"), exist_ok=True)
        p = os.path.join(d, "app.py")
        open(p, "w", encoding="utf-8").write("import streamlit as st\nst.title('x')\n")
        req = os.path.join(d, "requirements.txt")
        open(req, "w", encoding="utf-8").write("streamlit\n")
        assert syntax_check(d) == {}
        std, third = detect_imports(d)
        assert "streamlit" in third
        patched = patch_requirements(d, third)
        assert "streamlit" in patched
        t = write_smoke_test(d)
        assert os.path.exists(t)

