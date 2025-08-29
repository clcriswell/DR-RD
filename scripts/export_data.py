#!/usr/bin/env python
from __future__ import annotations

import argparse
import yaml

from dr_rd.privacy import export, subject


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    t = sub.add_parser("tenant")
    t.add_argument("--org", required=True)
    t.add_argument("--ws", required=True)
    s = sub.add_parser("subject")
    s.add_argument("--org", required=True)
    s.add_argument("--ws", required=True)
    s.add_argument("--subject_key")
    s.add_argument("--email")
    s.add_argument("--user_id")
    args = p.parse_args()
    cfg = yaml.safe_load(open("config/retention.yaml"))
    if args.mode == "tenant":
        path = export.export_tenant((args.org, args.ws))
        print(path)
    else:
        if args.subject_key:
            key = args.subject_key
        else:
            fields = cfg.get("privacy", {}).get("identifiers", {}).get("fields", [])
            salt_env = cfg.get("privacy", {}).get("identifiers", {}).get("subject_salt_env", "PRIVACY_SALT")
            data = {k: v for k, v in {"email": args.email, "user_id": args.user_id}.items() if v}
            key = subject.derive_subject_key(data, fields, salt_env)
        path = export.export_subject((args.org, args.ws), key)
        print(path)


if __name__ == "__main__":
    main()
