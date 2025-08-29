import argparse
import subprocess

from . import get_version

def main(argv=None):
    parser = argparse.ArgumentParser(prog="dr-rd")
    parser.add_argument("--version", action="store_true", help="Print package version and exit")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("version", help="Print package version")

    demo_p = sub.add_parser("demo", help="Run demo scenarios")
    demo_p.add_argument(
        "name",
        choices=["specialists", "dynamic", "compliance", "rag", "all"],
        help="Demo name",
    )
    
    sub.add_parser("app", help="Launch Streamlit app")

    args = parser.parse_args(argv)

    if args.version or args.cmd == "version":
        print(get_version())
        return 0
    if args.cmd == "demo":
        if args.name == "all":
            return subprocess.call([
                "python",
                "scripts/demo_run.py",
                "--flow",
                "all",
                "--out",
                "samples/runs/cli",
                "--flags",
                "RAG_ENABLED=0,EVALUATORS_ENABLED=1",
            ])
        from scripts.demos import demo_specialists, demo_dynamic, demo_compliance, demo_rag

        mapping = {
            "specialists": demo_specialists,
            "dynamic": demo_dynamic,
            "compliance": demo_compliance,
            "rag": demo_rag,
        }
        return mapping[args.name].main()
    if args.cmd == "app":
        return subprocess.call(["python", "-m", "streamlit", "run", "app.py"])

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
