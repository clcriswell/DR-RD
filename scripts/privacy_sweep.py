#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import datetime
import yaml

from dr_rd.privacy import retention


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--org", default="default")
    p.add_argument("--ws", default="default")
    args = p.parse_args()
    cfg = yaml.safe_load(open("config/retention.yaml"))
    retention.sweep_ttl((args.org, args.ws), datetime.utcnow(), cfg)
    retention.scrub_pii((args.org, args.ws), cfg)


if __name__ == "__main__":
    main()
