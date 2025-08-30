import os
import subprocess
import time

import pytest
import requests

from e2e.config import APP_BASE_URL, APP_START_CMD, APP_START_TIMEOUT_SEC


def _wait_ready(url: str, timeout: int) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code in (200, 403):
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("app not ready")


@pytest.fixture(scope="session", autouse=True)
def app_server():
    ext = os.getenv("APP_EXTERNAL", "0") == "1"
    if ext:
        yield
        return
    proc = subprocess.Popen(APP_START_CMD, shell=True)
    try:
        _wait_ready(APP_BASE_URL, APP_START_TIMEOUT_SEC)
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


@pytest.fixture(scope="session")
def base_url():
    return APP_BASE_URL
