"""ckc-axiom-check: cross-check a commit's proof status against the kernel (opt-in).

If a commit declares `Status: math.machine-checked` and names Lean declarations in a `Lean:`
footer, this runs the lean-math `axiom-report` on those declarations and rejects the commit if
any of them is not `clean` (i.e. the kernel sees a `sorryAx` or a cited axiom). It also flags a
`math.axiomatised` commit whose named declarations are actually clean or open.

A `math.axiomatised` commit is additionally held to statement fidelity (spec v0.2.0 rule 14):
the kernel can vouch for the statement as written, not that the transcription matches the source,
so the commit must carry a `Source-Ref:` footer (anchoring the Lean statement to the cited work
and locus: theorem, equation, or page; `Paper-Ref:` is a deprecated alias, removed in v0.4.0) and
a `Refutation-Attempt:` footer (naming the artifact of an attempt to refute the transcribed
statement). This check needs no Lean toolchain and runs before `axiom-report` is looked up;
missing footers reject the commit even when the kernel check would be skipped.

This extends the lean-math honesty gate from the working tree into the commit log. It is opt-in:
it needs Lean, a built project, and `axiom-report` on PATH (or `$CKC_AXIOM_REPORT`). When that is
unavailable it skips (the statement-fidelity gate above still applies), unless `--require` is
given.

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
    """Run axiom-report and return {decl: status} for the named declarations.

    The child environment is scrubbed of GIT_* variables: as a commit-msg hook we
    inherit git's hook environment (GIT_DIR, GIT_INDEX_FILE, ...), and when the commit
    happens inside a `git worktree` those leak into lake's own git operations, making
    lake conclude the `.lake/packages` clones are foreign and wipe/re-clone them.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run(
        [report_bin, project, *names],
        capture_output=True, text=True, check=False, env=env,
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
    if status not in ("math.machine-checked", "math.axiomatised"):
        return 0

    # statement-fidelity gate (math.axiomatised only, checked BEFORE the kernel is consulted:
    # it needs no Lean toolchain and must not be bypassable by an unavailable axiom-report).
    if status == "math.axiomatised":
        source_ref = (c.footer("Source-Ref") or "").strip()
        paper_ref = (c.footer("Paper-Ref") or "").strip()  # deprecated alias, one release
        missing = []
        if not (source_ref or paper_ref):
            missing.append("Source-Ref:")
        if not (c.footer("Refutation-Attempt") or "").strip():
            missing.append("Refutation-Attempt:")
        if missing:
            print("ckc-axiom-check: Status is math.axiomatised but the commit is missing "
                  f"required statement-fidelity footer(s): {', '.join(missing)} "
                  "(spec v0.2.0 rule 14).", file=sys.stderr)
            print("  The kernel is honest about the statement as written, not that the "
                  "transcription matches the source. Every cited axiom needs a source anchor "
                  "(Source-Ref: <work, locus> — a theorem, equation, or page; Paper-Ref: is a "
                  "deprecated alias) and a refutation-attempt artifact "
                  "(Refutation-Attempt: <path to the attempt>).", file=sys.stderr)
            print("  See the axiom admission protocol (WORKFLOW.md) and the axiom-faithfulness "
                  "reference in the lean-math proof-review skill.", file=sys.stderr)
            return 1
        if paper_ref and not source_ref:
            print("ckc-axiom-check: Paper-Ref: is deprecated for Source-Ref: and will be "
                  "removed in v0.4.0.", file=sys.stderr)

    if not names:
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
