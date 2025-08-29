import argparse
from . import demo_specialists, demo_dynamic, demo_compliance, demo_rag


def main(argv=None):
    parser = argparse.ArgumentParser(prog="dr-rd-demo")
    parser.add_argument("name", choices=["specialists", "dynamic", "compliance", "rag"], help="Demo name")
    args = parser.parse_args(argv)
    mapping = {
        "specialists": demo_specialists,
        "dynamic": demo_dynamic,
        "compliance": demo_compliance,
        "rag": demo_rag,
    }
    return mapping[args.name].main()


if __name__ == "__main__":
    raise SystemExit(main())
