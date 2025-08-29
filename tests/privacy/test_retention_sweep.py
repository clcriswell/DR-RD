from datetime import datetime, timedelta
from pathlib import Path
import os

from dr_rd.privacy import retention
import yaml

CFG = yaml.safe_load(open("config/retention.yaml"))


def test_sweep_ttl(tmp_path):
    tenant = ("o", "w")
    root = Path.home() / ".dr_rd" / "tenants" / "o" / "w" / "kb"
    root.mkdir(parents=True, exist_ok=True)
    old_file = root / "old.txt"
    old_file.write_text("hi")
    old_time = datetime.utcnow() - timedelta(days=400)
    old_ts = old_time.timestamp()
    os.utime(old_file, (old_ts, old_ts))
    report = retention.sweep_ttl(tenant, datetime.utcnow(), CFG)
    assert report["kb"] >= 1
