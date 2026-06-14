"""ckc-lint: validate a commit message file against CKC.

Usage:
    ckc-lint [--strict] [--quiet] <commit-msg-file>
    ckc-lint --message "<text>"

Exit codes: 0 ok (warnings allowed), 1 errors (or warnings under --strict), 2 usage.
Designed as a `commit-msg` hook: pre-commit passes the message file as the argument.
"""
from __future__ import annotations

import argparse
import sys

from .parse import parse
from .rules import check

RED = "\033[31m"
YEL = "\033[33m"
GRN = "\033[32m"
DIM = "\033[2m"
RST = "\033[0m"


def _color(s: str, code: str, on: bool) -> str:
    return f"{code}{s}{RST}" if on else s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ckc-lint", description="Validate a commit message against CKC.")
    ap.add_argument("file", nargs="?", help="path to the commit message file")
    ap.add_argument("--message", "-m", help="lint this message text instead of a file")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--quiet", action="store_true", help="print nothing on success")
    args = ap.parse_args(argv)

    if args.message is not None:
        text = args.message
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            print(f"ckc-lint: cannot read {args.file}: {e}", file=sys.stderr)
            return 2
    else:
        ap.print_usage(sys.stderr)
        return 2

    on = sys.stderr.isatty()
    issues = check(parse(text))
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]

    for i in errors:
        print(f"{_color('error', RED, on)}  {i.message}", file=sys.stderr)
    for i in warnings:
        print(f"{_color('warning', YEL, on)}  {i.message}", file=sys.stderr)

    if errors or (args.strict and warnings):
        print(_color("commit message rejected by ckc-lint "
                     "(https://hotherio.github.io/conventional-knowledge-commits/)", DIM, on),
              file=sys.stderr)
        return 1
    if not args.quiet and not issues:
        print(_color("ckc-lint: ok", GRN, on), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
