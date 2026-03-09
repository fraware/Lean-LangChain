from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(prog="obr")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("open-environment")
    sub.add_parser("create-session")
    sub.add_parser("run-patch-obligation")
    sub.add_parser("run-protocol-obligation")
    sub.add_parser("review")
    sub.add_parser("artifacts")
    sub.add_parser("regressions")

    args = parser.parse_args()
    print(json.dumps({"status": "stub", "command": args.cmd}, indent=2))


if __name__ == "__main__":
    main()
