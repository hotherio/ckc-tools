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
    ("axiomatised with Source-Ref fidelity footers",
     "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)\n"
     "Source-Ref: Braess & Hackbusch 2005, Thm 3.1, p.417\n"
     "Refutation-Attempt: Refutations/F00_expSumRank_logBound.lean", 0, 0),
    ("axiomatised with Paper-Ref alias satisfies the anchor nudge",
     "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)\n"
     "Paper-Ref: Braess & Hackbusch 2005, Thm 3.1, p.417\n"
     "Refutation-Attempt: Refutations/F00_expSumRank_logBound.lean", 0, 0),
    ("axiomatised without fidelity footers (warn x2)",
     "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)", 0, 2),
    ("sci.measured citing Pre-Registration without Protocol-Deviations (warn)",
     "experiment(x): run it\n\nStatus: sci.measured\nMetric: MSE\n"
     "Pre-Registration: OSF osf.io/7k2mq", 0, 1),
    ("sci.supported citing Protocol without Protocol-Deviations (warn)",
     "result(x): report it\n\nStatus: sci.supported\n"
     "Protocol: protocols/P-2026-003.md", 0, 1),
    ("sci.measured with Protocol-Deviations: none (clean)",
     "experiment(x): run it\n\nStatus: sci.measured\nMetric: MSE\n"
     "Pre-Registration: OSF osf.io/7k2mq\nProtocol-Deviations: none", 0, 0),
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
    # CLI / conventional-pre-commit-compatibility cases: (label, argv, expected_exit)
    from ckc_lint.cli import main as cli_main
    cli_cases = [
        ("cli: plain feat ok", ["--message", "feat(api): x"], 0),
        ("cli: positional types restrict (experiment not allowed)",
         ["feat", "fix", "--message", "experiment(x): y"], 1),
        ("cli: positional types allow listed", ["feat", "fix", "--message", "fix(x): y"], 0),
        ("cli: autosquash allowed by default", ["--message", "fixup! earlier commit"], 0),
        ("cli: autosquash rejected under --strict", ["--strict", "--message", "fixup! earlier"], 1),
        ("cli: merge allowed by default", ["--message", "Merge branch 'main'"], 0),
        ("cli: --force-scope requires scope", ["--force-scope", "--message", "feat: x"], 1),
        ("cli: --force-scope ok with scope", ["--force-scope", "--message", "feat(api): x"], 0),
        ("cli: --scopes rejects unlisted", ["--scopes", "api,ui", "--message", "feat(db): x"], 1),
        ("cli: --scopes accepts listed", ["--scopes", "api,ui", "--message", "feat(api): x"], 0),
        ("cli: CKC type ok by default", ["--message", "formalize(x): close\n\nLean: A.b\nStatus: math.machine-checked\nAxioms: propext"], 0),
    ]
    cli_fail = 0
    for label, argv, exp in cli_cases:
        rc = cli_main(argv + ["--quiet"])
        ok = rc == exp
        print(f"  [{'ok  ' if ok else 'FAIL'}] {label}  (exit={rc} exp={exp})")
        if not ok:
            cli_fail += 1

    # ckc-axiom-check: the axiom-report child env must be scrubbed of GIT_* (a commit-msg
    # hook inherits git's hook env; inside a worktree the leak makes lake wipe .lake/packages).
    import os
    from unittest import mock

    from ckc_axiom_check.cli import _statuses
    env_fail = 0
    os.environ["GIT_DIR"] = "/tmp/ckc-test-fake-gitdir"
    try:
        with mock.patch("ckc_axiom_check.cli.subprocess.run") as m:
            m.return_value = mock.Mock(stdout="", returncode=0)
            _statuses("fake-axiom-report", ".", ["Foo.bar"])
            child_env = m.call_args.kwargs.get("env")
            ok = child_env is not None and not any(k.startswith("GIT_") for k in child_env)
    finally:
        del os.environ["GIT_DIR"]
    print(f"  [{'ok  ' if ok else 'FAIL'}] axiom-check: GIT_* scrubbed from axiom-report env")
    if not ok:
        env_fail = 1

    # the protocol-fidelity nudge is silenced by a Protocol-Deviations: footer (the warning
    # floor above cannot assert absence, so check the specific message directly)
    protocol_fail = 0
    issues = check(parse(
        "experiment(x): run it\n\nStatus: sci.measured\nMetric: MSE\n"
        "Pre-Registration: OSF osf.io/7k2mq\nProtocol-Deviations: none"))
    ok = not any("Protocol-Deviations" in i.message for i in issues)
    print(f"  [{'ok  ' if ok else 'FAIL'}] lint: Protocol-Deviations: none silences the protocol-fidelity nudge")
    if not ok:
        protocol_fail = 1

    # ckc-axiom-check: the statement-fidelity gate on math.axiomatised commits runs BEFORE
    # axiom-report is looked up, so it is testable (and fast-fails) without a Lean toolchain.
    import contextlib
    import io
    import tempfile

    from ckc_axiom_check.cli import main as axiom_main
    DEPRECATION = "Paper-Ref: is deprecated for Source-Ref: and will be removed in v0.4.0"
    # (label, message, expected_exit, deprecation_notice_expected: True | False | None=don't care)
    fidelity_cases = [
        ("axiom-check: axiomatised missing fidelity footers exits 1",
         "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)\n", 1, None),
        ("axiom-check: axiomatised missing only Refutation-Attempt exits 1",
         "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)\n"
         "Source-Ref: Braess & Hackbusch 2005, Thm 3.1, p.417\n", 1, None),
        ("axiom-check: axiomatised with no source anchor exits 1",
         "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)\n"
         "Refutation-Attempt: Refutations/F00_expSumRank_logBound.lean\n", 1, None),
        ("axiom-check: axiomatised with Source-Ref passes, no deprecation notice",
         "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)\n"
         "Source-Ref: Braess & Hackbusch 2005, Thm 3.1, p.417\n"
         "Refutation-Attempt: Refutations/F00_expSumRank_logBound.lean\n", 0, False),
        ("axiom-check: Paper-Ref alias passes the gate with a deprecation notice",
         "axiomatize~(x): cite\n\nLean: A.b\nStatus: math.axiomatised\nAXIOM: A.b (x)\n"
         "Paper-Ref: Braess & Hackbusch 2005, Thm 3.1, p.417\n"
         "Refutation-Attempt: Refutations/F00_expSumRank_logBound.lean\n", 0, True),
        ("axiom-check: machine-checked unaffected by fidelity gate",
         "formalize(x): close it\n\nLean: A.b\nStatus: math.machine-checked\n"
         "Axioms: propext\n", 0, None),
    ]
    fid_fail = 0
    for label, msg, exp, dep in fidelity_cases:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            tf.write(msg)
            path = tf.name
        stderr = io.StringIO()
        try:
            with mock.patch("ckc_axiom_check.cli._find_axiom_report", return_value=None), \
                    contextlib.redirect_stderr(stderr):
                rc = axiom_main([path])
        finally:
            os.unlink(path)
        ok = rc == exp
        if dep is not None:
            ok = ok and ((DEPRECATION in stderr.getvalue()) == dep)
        print(f"  [{'ok  ' if ok else 'FAIL'}] {label}  (exit={rc} exp={exp})")
        if not ok:
            fid_fail += 1

    total = len(CASES) + len(PROFILE_CASES) + len(cli_cases) + 2 + len(fidelity_cases)
    failures += cli_fail + env_fail + protocol_fail + fid_fail
    print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
