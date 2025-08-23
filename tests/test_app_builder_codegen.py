from app_builder.codegen import render_streamlit_app
from app_builder.spec import AppSpec, PageSpec


def test_codegen_generates_expected_files():
    spec = AppSpec(
        name="Test App",
        description="Demo",
        pages=[PageSpec(name="Home", purpose="Start here")],
    )
    files = render_streamlit_app(spec)
    keys = list(files.keys())
    assert any(k.endswith("/app.py") for k in keys)
    assert any("/pages/Home.py" in k for k in keys)
    assert any(k.endswith("/requirements.txt") for k in keys)
