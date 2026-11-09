"""ZombieCheck CLI.

zombiecheck check   input.csv -o out.csv [--limit N] [--resume]
zombiecheck source  --out rows.csv [--limit 600]     (awesome-go, 2,902 rows)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .client import TinyFishClient
from .runner import read_input, run_rows
from .source import fetch_awesome_go, rows_to_csv

EXIT_OK, EXIT_USAGE, EXIT_FETCH = 0, 2, 3


def _cmd_source(args) -> int:
    rows = fetch_awesome_go()[: args.limit or None]
    Path(args.out).write_text(rows_to_csv(rows))
    print(f"wrote {len(rows)} rows to {args.out}")
    return EXIT_OK


def _cmd_check(args) -> int:
    rows = read_input(args.input)
    if not rows:
        print("error: no rows with URLs in input", file=sys.stderr)
        return EXIT_USAGE
    client = TinyFishClient(retries=args.retries, verbose=args.verbose)
    checkpoint = Path(args.output + ".checkpoint.json")
    if not (args.resume and checkpoint.exists()):
        checkpoint.unlink(missing_ok=True)
    results = run_rows(
        client, rows, Path(args.output), checkpoint, limit=args.limit, verbose=args.verbose
    )
    from collections import Counter

    print(
        json.dumps(
            {
                "checked": len(results),
                "counts": dict(Counter(r["verdict"] for r in results)),
            }
        )
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="ZombieCheck: alive / slowing_down / zombie per row."
    )
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check", help="verify a CSV of name,url rows")
    c.add_argument("input")
    c.add_argument("-o", "--output", default="zombie-report.csv")
    c.add_argument("--limit", type=int, default=None)
    c.add_argument(
        "--resume", action="store_true", help="skip rows already in the checkpoint"
    )
    c.add_argument("--retries", type=int, default=3)
    c.add_argument("--verbose", action="store_true")
    s = sub.add_parser("source", help="fetch the awesome-go list as rows.csv")
    s.add_argument("--out", default="rows.csv")
    s.add_argument("--limit", type=int, default=600)
    ap.add_argument("--version", action="version", version=f"zombicheck {__version__}")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    import os

    if not os.getenv("TINYFISH_API_KEY"):
        print("error: TINYFISH_API_KEY is not set", file=sys.stderr)
        return EXIT_USAGE
    try:
        return _cmd_source(args) if args.command == "source" else _cmd_check(args)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_FETCH


if __name__ == "__main__":
    raise SystemExit(main())
