import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rotate SHARE_SECRET for share links")
    parser.add_argument("--show-instructions", action="store_true", help="Display rotation steps")
    args = parser.parse_args(argv)
    if not args.show_instructions:
        parser.print_help()
        return 0
    print("Set a new value for SHARE_SECRET in your secrets store or environment.")
    print("Existing share links will stop working once rotated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
