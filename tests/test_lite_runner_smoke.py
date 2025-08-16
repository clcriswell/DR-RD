def test_lite_import():
    import app.lite_runner as lr
    assert callable(lr.render_lite)
