"""CLI wrapper around incident bundle generation."""
from __future__ import annotations

import argparse

from dr_rd.incidents.bundle import make_incident_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Create incident bundle")
    parser.add_argument("--base", required=True, help="Base run directory")
    parser.add_argument("--cand", required=True, help="Candidate run directory")
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    path = make_incident_bundle(args.base, args.cand, args.out)
    print(path)


if __name__ == "__main__":
    main()
