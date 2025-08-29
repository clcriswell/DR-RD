#!/usr/bin/env python
from __future__ import annotations

import argparse
import yaml

from dr_rd.privacy import subject, erasure


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--org", required=True)
    p.add_argument("--ws", required=True)
    p.add_argument("--email")
    p.add_argument("--user_id")
    p.add_argument("--subject_key")
    p.add_argument("--reason", default="user_request")
    args = p.parse_args()

    cfg = yaml.safe_load(open("config/retention.yaml"))
    fields = cfg.get("privacy", {}).get("identifiers", {}).get("fields", [])
    salt_env = cfg.get("privacy", {}).get("identifiers", {}).get("subject_salt_env", "PRIVACY_SALT")

    if args.subject_key:
        key = args.subject_key
    else:
        data = {k: v for k, v in {"email": args.email, "user_id": args.user_id}.items() if v}
        key = subject.derive_subject_key(data, fields, salt_env)
    erasure.mark_subject_for_erasure((args.org, args.ws), key, args.reason, "cli")
    erasure.execute_erasure((args.org, args.ws), key, cfg)


if __name__ == "__main__":
    main()
