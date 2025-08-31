# Streamlit E2E CI

The end-to-end tests exercise the Streamlit app through Playwright. In CI the workflow:

1. installs dependencies and browsers.
2. starts `streamlit run app.py --server.port 8501 --server.headless true` with output redirected to `app.log`.
3. polls `http://localhost:8501` until ready.
4. runs `pytest -q e2e` under Xvfb.
5. uploads `app.log` as an artifact if tests fail.

To reproduce locally:

```bash
# in one shell
streamlit run app.py --server.port 8501 --server.headless true

# in another shell
APP_EXTERNAL=1 pytest -q e2e
```
