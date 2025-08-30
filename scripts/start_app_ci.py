import os
import subprocess
import sys
import time

import requests

from e2e.config import APP_BASE_URL, APP_START_CMD, APP_START_TIMEOUT_SEC


if __name__ == "__main__":
    proc = subprocess.Popen(APP_START_CMD, shell=True)
    t0 = time.time()
    while time.time() - t0 < APP_START_TIMEOUT_SEC:
        try:
            if requests.get(APP_BASE_URL, timeout=2).status_code in (200, 403):
                print("app ready")
                sys.exit(0)
        except Exception:
            time.sleep(1)
    proc.terminate()
    sys.exit(1)
