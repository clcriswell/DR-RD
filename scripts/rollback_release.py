#!/usr/bin/env python3
import subprocess


def main() -> None:
    tags = subprocess.check_output(["git", "tag"]).decode().splitlines()
    if not tags:
        print("No release tags found")
        return
    last = tags[-1]
    print(f"Run 'git checkout {last}' to rollback to the previous release tag.")
    print("Verify config lock and restart demos/smoke tests afterwards.")


if __name__ == "__main__":
    main()
