import argparse
import json
from pathlib import Path

FLAGS_PATH = Path('.dr_rd/flags.json')


def load() -> dict:
    if FLAGS_PATH.exists():
        return json.loads(FLAGS_PATH.read_text(encoding='utf-8'))
    return {"version": 1, "flags": {}}


def save(data: dict) -> None:
    FLAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = FLAGS_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
    tmp.replace(FLAGS_PATH)


def list_flags() -> None:
    data = load().get('flags', {})
    for k, v in data.items():
        print(f"{k}: {v}")


def set_flag(name: str, value: bool) -> None:
    data = load()
    data.setdefault('flags', {})[name] = value
    save(data)
    print(f"{name} set to {value}")


def main() -> None:
    p = argparse.ArgumentParser(description='Edit feature flags')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list')
    en = sub.add_parser('enable')
    en.add_argument('name')
    dis = sub.add_parser('disable')
    dis.add_argument('name')
    args = p.parse_args()
    if args.cmd == 'list':
        list_flags()
    elif args.cmd == 'enable':
        set_flag(args.name, True)
    elif args.cmd == 'disable':
        set_flag(args.name, False)


if __name__ == '__main__':
    main()
