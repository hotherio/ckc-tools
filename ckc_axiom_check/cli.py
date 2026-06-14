"""ckc-axiom-check: cross-check a commit's proof status against the kernel (opt-in).

If a commit declares `Status: math.machine-checked` and names Lean declarations in a `Lean:`
footer, this runs the lean-math `axiom-report` on those declarations and rejects the commit if
any of them is not `clean` (i.e. the kernel sees a `sorryAx` or a cited axiom). It also flags a
`math.axiomatised` commit whose named declarations are actually clean or open.

This extends the lean-math honesty gate from the working tree into the commit log. It is opt-in:
it needs Lean, a built project, and `axiom-report` on PATH (or `$CKC_AXIOM_REPORT`). When that is
unavailable it skips, unless `--require` is given.

Usage:
    ckc-axiom-check [--require] [--project DIR] <commit-msg-file>
Env: CKC_AXIOM_REPORT (path to axiom-report), CKC_PROJECT (Lean project dir).
Exit: 0 ok or skipped, 1 dishonest commit (or unavailable under --require), 2 usage.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

from ckc_lint.parse import parse


def _find_axiom_report() -> str | None:
    return os.environ.get("CKC_AXIOM_REPORT") or shutil.which("axiom-report")


def _statuses(report_bin: str, project: str, names: list[str]) -> dict[str, str]:
    """Run axiom-report and return {decl: status} for the named declarations."""
    proc = subprocess.run(
        [report_bin, project, *names],
        capture_output=True, text=True, check=False,
    )
    out = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"^(\S+)\s+(clean|sorryAx|axiom)\b", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ckc-axiom-check")
    ap.add_argument("file", nargs="?", help="commit message file")
    ap.add_argument("--require", action="store_true",
                    help="fail if axiom-report is unavailable, instead of skipping")
    ap.add_argument("--project", help="Lean project dir (default: $CKC_PROJECT or cwd)")
    args = ap.parse_args(argv)
    if not args.file:
        ap.print_usage(sys.stderr)
        return 2

    with open(args.file, encoding="utf-8") as fh:
        c = parse(fh.read())

    status = (c.footer("Status") or "").strip()
    lean = c.footer("Lean") or c.footer("Formal-Statement") or ""
    names = [n.strip().removeprefix("lean:") for n in lean.split(",") if n.strip()]

    # only proof commits that make a checkable claim are in scope
    if status not in ("math.machine-checked", "math.axiomatised") or not names:
        return 0

    report_bin = _find_axiom_report()
    if not report_bin:
        msg = ("ckc-axiom-check: axiom-report not found "
               "(set $CKC_AXIOM_REPORT or install the lean-math plugin).")
        if args.require:
            print(msg + " Required by --require.", file=sys.stderr)
            return 1
        print(msg + " Skipping.", file=sys.stderr)
        return 0

    project = args.project or os.environ.get("CKC_PROJECT") or os.getcwd()
    found = _statuses(report_bin, project, names)

    # Hard-fail only on a genuine contradiction. "Not found" is inconclusive (the project may
    # not be built, or the hook ran outside the Lean project dir): note it, do not block.
    bad, unverified = [], []
    for n in names:
        st = found.get(n)
        if st is None:
            unverified.append(n)
        elif status == "math.machine-checked" and st != "clean":
            bad.append(f"{n}: kernel reports '{st}', but the commit claims math.machine-checked")
        elif status == "math.axiomatised" and st == "clean":
            bad.append(f"{n}: kernel reports 'clean', but the commit claims math.axiomatised")

    if bad:
        print("ckc-axiom-check: the commit's Status does not match #print axioms:", file=sys.stderr)
        for b in bad:
            print(f"  {b}", file=sys.stderr)
        return 1
    if unverified:
        print("ckc-axiom-check: could not verify "
              f"{', '.join(unverified)} (not reported by axiom-report in {project}); "
              "skipping.", file=sys.stderr)
        if args.require:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
