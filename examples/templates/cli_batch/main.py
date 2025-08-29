import argparse
import json
from core.runner import execute_task


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input JSONL tasks")
    parser.add_argument("output", help="Output JSONL results")
    args = parser.parse_args(argv)

    with open(args.input) as src, open(args.output, "w") as dst:
        for line in src:
            if not line.strip():
                continue
            task = json.loads(line)
            result = execute_task(**task)
            dst.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
