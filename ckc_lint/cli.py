"""ckc-lint: validate a commit message against CKC.

A drop-in superset of compilerla/conventional-pre-commit: it accepts the same interface, so an
existing `conventional-pre-commit` hook config (positional types plus --strict, --force-scope,
--scopes, --no-color, --verbose) can switch to `ckc` unchanged. On top of that it allows the CKC
vocabulary by default and runs the CKC checks (status values, trusted-base markers, ~ consistency,
relation footers).

Usage:
    ckc-lint [options] [types...] <commit-msg-file>
    ckc-lint [options] --message "<text>"
    ckc-lint --print-types [--profile P]

Exit codes: 0 ok, 1 rejected or file error, 2 usage.
"""
from __future__ import annotations

import argparse
import sys

from . import data
from .config import resolve_profiles
from .parse import parse
from .rules import Issue, check

RED, YEL, GRN, DIM, RST = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"
AUTOSQUASH = ("fixup! ", "squash! ", "amend! ")


def _c(s: str, code: str, on: bool) -> str:
    return f"{code}{s}{RST}" if on else s


def _first_line(text: str) -> str:
    return text.split("\n", 1)[0] if text else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ckc-lint", description="Validate a commit message against CKC.")
    # conventional-pre-commit-compatible positionals: optional types, then the input file.
    ap.add_argument("args", nargs="*",
                    help="optional list of allowed types, then the commit message file")
    # conventional-pre-commit-compatible flags
    ap.add_argument("--no-color", action="store_true", help="disable color in output")
    ap.add_argument("--force-scope", action="store_true", help="require the commit to have a scope")
    ap.add_argument("--scopes", help="comma-separated list of allowed scopes, e.g. api,client")
    ap.add_argument("--strict", action="store_true",
                    help="strict mode: reject fixup!/squash!/merge commits and treat CKC warnings as errors")
    ap.add_argument("--verbose", action="store_true", help="print more detail on failure")
    # CKC additions
    ap.add_argument("--message", "-m", help="lint this message text instead of a file")
    ap.add_argument("--profile", action="append",
                    help="active profile(s): proof, science, or both (repeatable or comma-separated)")
    ap.add_argument("--print-types", action="store_true",
                    help="print the allowed types as a YAML list (for conventional-pre-commit args) and exit")
    ap.add_argument("--quiet", action="store_true", help="print nothing on success")
    a = ap.parse_args(argv)

    profiles = resolve_profiles(a.profile)
    on = (not a.no_color) and sys.stderr.isatty()

    if a.print_types:
        print("[" + ", ".join(data.ordered_types(profiles)) + "]")
        return 0

    # Resolve positional types and the input file. The last positional is the file (as in
    # conventional-pre-commit); any earlier positionals are the explicit allowed-types list.
    types_override: list[str] | None = None
    if a.message is not None:
        text = a.message
        types_override = a.args or None
    else:
        if not a.args:
            print("ckc-lint: missing commit message file (or use --message)", file=sys.stderr)
            return 2
        path = a.args[-1]
        types_override = a.args[:-1] or None
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            print(f"ckc-lint: cannot read {path}: {e}", file=sys.stderr)
            return 1

    # fixup!/squash!/amend! and merge commits: allowed by default, rejected under --strict.
    first = _first_line(parse(text).raw)
    if first.startswith(AUTOSQUASH) or first.startswith("Merge "):
        if a.strict:
            print(_c("error", RED, on) + "  autosquash or merge commit rejected under --strict",
                  file=sys.stderr)
            return 1
        return 0

    c = parse(text)
    issues: list[Issue] = check(c, profiles, allowed_types=types_override)

    # scope checks (conventional-pre-commit parity)
    if c.header_ok:
        if a.force_scope and not c.scope:
            issues.append(Issue("error", "a scope is required (--force-scope)"))
        if a.scopes and c.scope:
            allowed = {s.strip() for s in a.scopes.split(",") if s.strip()}
            if c.scope not in allowed:
                issues.append(Issue("error",
                    f"scope '{c.scope}' is not in the allowed scopes: {', '.join(sorted(allowed))}"))

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    for i in errors:
        print(f"{_c('error', RED, on)}  {i.message}", file=sys.stderr)
    for i in warnings:
        print(f"{_c('warning', YEL, on)}  {i.message}", file=sys.stderr)

    if errors or (a.strict and warnings):
        if a.verbose:
            print(_c("the message was:", DIM, on), file=sys.stderr)
            print(text.strip(), file=sys.stderr)
        print(_c("commit message rejected by ckc-lint "
                 "(https://hotherio.github.io/conventional-knowledge-commits/)", DIM, on),
              file=sys.stderr)
        return 1
    if not a.quiet and not issues:
        print(_c("ckc-lint: ok", GRN, on), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
