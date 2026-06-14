#!/usr/bin/env python3
"""Dependency-free test runner for ckc_lint. Run: python3 tests/run.py

Each case is (label, message, expected_errors, expected_warnings_at_least).
We assert the error count exactly and that warnings meet a floor, so the suite stays
robust to added nudges.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ckc_lint.parse import parse  # noqa: E402
from ckc_lint.rules import check  # noqa: E402

CASES = [
    # label, message, expected_errors, min_warnings
    ("plain CC feat (mixed repo)", "feat(api): add pagination", 0, 0),
    ("plain CC fix with body", "fix: handle null\n\nA longer description.", 0, 0),
    ("CKC proof, machine-checked clean",
     "formalize(fubini): close the d-fold factorization\n\n"
     "Lean: IGL.fubini_factorization\nStatus: math.machine-checked\n"
     "Axioms: propext, Classical.choice, Quot.sound\nCloses: conjecture:master-formula", 0, 0),
    ("CKC axiomatize with ~ and AXIOM",
     "axiomatize~(exp-sum): cite the rank bound\n\n"
     "Lean: IGL.expSumRank_logBound\nStatus: math.axiomatised\n"
     "AXIOM: IGL.expSumRank_logBound (rank K = O(log 1/e))", 0, 0),
    ("CKC refute breaking",
     "refute(separability)!: counterexample\n\n"
     "Disproves: conjecture:naive-separable\nStatus: math.disproved\n"
     "BREAKING CHANGE: conjecture:naive-separable withdrawn", 0, 0),
    ("CKC science experiment",
     "experiment(non-additive): K=1 vs K>1\n\nStatus: sci.measured\nMetric: MSE", 0, 0),
    ("unknown type", "frobnicate: do a thing", 1, 0),
    ("bad header (no colon space)", "feat:no space", 1, 0),
    ("unknown status value",
     "formalize(x): close it\n\nLean: A.b\nStatus: math.totally-proved", 1, 0),
    ("lowercase axiom token",
     "axiomatize~(x): cite\n\nStatus: math.axiomatised\naxiom: Foo.bar (why)", 1, 0),
    ("tilde without trusted-base footer (warn)",
     "formalize~(x): close it\n\nStatus: math.machine-checked\nAxioms: propext", 0, 1),
    ("axiomatised without AXIOM footer (warn)",
     "axiomatize~(x): cite\n\nStatus: math.axiomatised\nAXIOM: A.b (x)\nLean: A.b", 0, 0),
    ("machine-checked without Axioms (warn)",
     "formalize(x): close it\n\nLean: A.b\nStatus: math.machine-checked", 0, 1),
]

# (label, message, expected_errors, min_warnings, profiles)
PROFILE_CASES = [
    ("science-only rejects formalize", "formalize(x): close it", 1, 0, {"science"}),
    ("science-only allows experiment", "experiment(x): run it\n\nStatus: sci.measured", 0, 0, {"science"}),
    ("proof-only rejects experiment", "experiment(x): run it", 1, 0, {"proof"}),
    ("proof-only allows formalize", "formalize(x): close it\n\nLean: A.b\nStatus: math.machine-checked\nAxioms: propext", 0, 0, {"proof"}),
    ("either profile allows shared conjecture", "conjecture(x): a claim", 0, 0, {"science"}),
    ("either profile allows plain feat", "feat(x): tooling", 0, 0, {"proof"}),
]


def run() -> int:
    failures = 0
    for case in CASES + [(l, m, e, w) for (l, m, e, w, _p) in PROFILE_CASES]:
        label, msg, exp_err, min_warn = case
        profiles = None
        for pc in PROFILE_CASES:
            if pc[0] == label:
                profiles = pc[4]
                break
        issues = check(parse(msg), profiles)
        errs = sum(1 for i in issues if i.level == "error")
        warns = sum(1 for i in issues if i.level == "warning")
        ok = (errs == exp_err) and (warns >= min_warn)
        mark = "ok  " if ok else "FAIL"
        print(f"  [{mark}] {label}  (errors={errs} exp={exp_err}, warnings={warns} min={min_warn})")
        if not ok:
            failures += 1
            for i in issues:
                print(f"         {i.level}: {i.message}")
    total = len(CASES) + len(PROFILE_CASES)
    print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
