"""Structural CKC checks over a parsed commit. Pure: returns issues, prints nothing."""
from __future__ import annotations

from dataclasses import dataclass

from . import data
from .parse import Commit


@dataclass
class Issue:
    level: str  # "error" | "warning"
    message: str


def check(c: Commit) -> list[Issue]:
    issues: list[Issue] = []

    # 1. valid Conventional Commit header
    if not c.header_ok or not c.type:
        issues.append(Issue("error",
            "header is not a valid Conventional Commit: expected "
            "'type[(scope)][~][!]: description'"))
        return issues  # nothing else is meaningful without a header

    # 2. type in the CKC union (case-insensitive, per spec rule 13)
    types = data.all_types()
    if c.type.lower() not in types:
        issues.append(Issue("error",
            f"unknown type '{c.type}'. Allowed CKC + Conventional Commits types: "
            f"{', '.join(sorted(types))}"))

    profile = data.profile_of(c.type.lower())

    # 3. Status footer value, if present, is a known namespaced status
    status = c.footer("Status")
    if status is not None:
        if status.strip() not in data.all_statuses():
            issues.append(Issue("error",
                f"unknown Status '{status.strip()}'. Use a math.* or sci.* value, e.g. "
                "math.machine-checked or sci.replicated."))

    # 4. trusted-base / breaking tokens must be uppercase when present
    lower_breaking = {t.lower() for t in data.breaking_tokens()}
    lower_tb = {t.lower() for t in data.trusted_base_tokens()}
    for f in c.footers:
        tl = f.token.lower()
        if tl in lower_breaking and f.token not in data.breaking_tokens():
            issues.append(Issue("error",
                f"'{f.token}' footer must be uppercase: write 'BREAKING CHANGE'."))
        if tl in lower_tb and f.token not in data.trusted_base_tokens():
            issues.append(Issue("error",
                f"'{f.token}' trusted-base footer must be uppercase, e.g. "
                f"'{f.token.upper()}'."))

    present_tb = [f for f in c.footers if f.token in data.trusted_base_tokens()]

    # 5. ~ consistency (spec rule 12): a convenience flag, so these are warnings
    if c.tilde and not present_tb:
        issues.append(Issue("warning",
            "'~' marks a trusted-base caveat but no AXIOM/OPEN/ASSUMES/UNREPLICATED footer is present."))
    if present_tb and not c.tilde:
        issues.append(Issue("warning",
            "a trusted-base footer is present; consider adding '~' before the ':' for at-a-glance reading."))

    # honesty nudges (warnings; the ckc-axiom-check hook enforces the proof case against the kernel)
    if status and status.strip() == "math.axiomatised" and not any(
            f.token == "AXIOM" for f in present_tb):
        issues.append(Issue("warning",
            "Status is math.axiomatised but there is no AXIOM: footer naming the cited axiom."))
    if status and status.strip() == "math.open" and not any(
            f.token == "OPEN" for f in present_tb):
        issues.append(Issue("warning",
            "Status is math.open but there is no OPEN: footer naming the gap."))

    # profile-specific nudge: machine-checked should record what was checked
    if status and status.strip() == "math.machine-checked" and c.footer("Axioms") is None:
        issues.append(Issue("warning",
            "Status is math.machine-checked but there is no Axioms: footer "
            "(should be the literal #print axioms output)."))

    return issues
