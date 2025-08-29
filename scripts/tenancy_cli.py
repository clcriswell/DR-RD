from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Optional

from dr_rd.tenancy import store
from core.security import auth


def _print(obj):
    if isinstance(obj, list):
        print(json.dumps([asdict(o) if not isinstance(o, dict) else o for o in obj]))
    else:
        print(json.dumps(asdict(obj) if not isinstance(obj, dict) else obj))


def org_create(args):
    _print(store.create_org(args.name))


def org_list(args):
    _print(store.list_orgs())


def ws_create(args):
    _print(store.create_workspace(args.org, args.name))


def ws_list(args):
    _print(store.list_workspaces(args.org))


def key_create(args):
    rec, secret = auth.create_api_key(args.org, args.ws, roles=args.roles)
    out = asdict(rec)
    out["secret"] = secret
    _print(out)


def key_revoke(args):
    # naive revoke by appending disabled record; for demo only
    principals = auth._read_all()  # type: ignore
    for rec in principals:
        if rec["key_id"] == args.key_id:
            rec["disabled"] = True
    auth.KEYS_PATH.write_text("".join(json.dumps(r) + "\n" for r in principals))
    _print({"revoked": args.key_id})


def principal_list(args):
    _print(store.list_principals(args.org, args.ws))


def main(argv: Optional[list[str]] = None):
    p = argparse.ArgumentParser(description="Tenancy management CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    org = sub.add_parser("org")
    org_sub = org.add_subparsers(dest="action", required=True)
    oc = org_sub.add_parser("create")
    oc.add_argument("name")
    oc.set_defaults(func=org_create)
    ol = org_sub.add_parser("list")
    ol.set_defaults(func=org_list)

    ws = sub.add_parser("ws")
    ws_sub = ws.add_subparsers(dest="action", required=True)
    wsc = ws_sub.add_parser("create")
    wsc.add_argument("--org", required=True)
    wsc.add_argument("name")
    wsc.set_defaults(func=ws_create)
    wsl = ws_sub.add_parser("list")
    wsl.add_argument("--org", required=True)
    wsl.set_defaults(func=ws_list)

    key = sub.add_parser("key")
    key_sub = key.add_subparsers(dest="action", required=True)
    kc = key_sub.add_parser("create")
    kc.add_argument("--org", required=True)
    kc.add_argument("--ws")
    kc.add_argument("--roles", nargs="*", default=["RUNNER"])
    kc.set_defaults(func=key_create)
    kr = key_sub.add_parser("revoke")
    kr.add_argument("--key-id", required=True)
    kr.set_defaults(func=key_revoke)

    pr = sub.add_parser("principal")
    pr_sub = pr.add_subparsers(dest="action", required=True)
    pl = pr_sub.add_parser("list")
    pl.add_argument("--org", required=True)
    pl.add_argument("--ws")
    pl.set_defaults(func=principal_list)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
