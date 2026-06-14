"""Parse a Conventional / CKC commit message into header, body, and footers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# type[~][(scope)][~!]: description
# The CKC '~' caveat flag attaches to the type (e.g. axiomatize~(exp-sum):); '!' keeps its
# Conventional Commits position before the colon. We also accept '~' before the colon, leniently.
HEADER_RE = re.compile(
    r"^(?P<type>[A-Za-z][\w-]*)"
    r"(?P<tilde1>~)?"
    r"(?:\((?P<scope>[^)]*)\))?"
    r"(?P<markers>[~!]*)"
    r": (?P<description>.+)$"
)

# a git trailer line: "Token: value" or "Token #value"; BREAKING CHANGE is the special token.
TRAILER_RE = re.compile(r"^(?P<token>BREAKING CHANGE|[A-Za-z][A-Za-z-]*)(?:: | #)(?P<value>.*)$")


@dataclass
class Footer:
    token: str
    value: str


@dataclass
class Commit:
    type: str | None = None
    scope: str | None = None
    tilde: bool = False
    bang: bool = False
    description: str | None = None
    body: str = ""
    footers: list[Footer] = field(default_factory=list)
    header_ok: bool = False
    raw: str = ""

    def footer(self, token: str) -> str | None:
        for f in self.footers:
            if f.token.lower() == token.lower():
                return f.value
        return None


def _strip_comments(text: str) -> str:
    """Drop git comment lines and anything after the diff scissors."""
    out = []
    for line in text.splitlines():
        if line.startswith("# ------------------------ >8"):
            break
        if line.startswith("#"):
            continue
        out.append(line)
    return "\n".join(out).strip("\n")


def parse(message: str) -> Commit:
    text = _strip_comments(message)
    c = Commit(raw=text)
    lines = text.split("\n")
    if not lines or not lines[0].strip():
        return c

    header = lines[0]
    m = HEADER_RE.match(header)
    if m:
        c.header_ok = True
        c.type = m.group("type")
        c.scope = m.group("scope")
        markers = m.group("markers") or ""
        c.tilde = bool(m.group("tilde1")) or "~" in markers
        c.bang = "!" in markers
        c.description = m.group("description")

    # split the remainder into paragraphs; the last paragraph is footers iff every
    # line is a trailer (or an indented continuation of one).
    rest = lines[1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    paragraphs: list[list[str]] = []
    cur: list[str] = []
    for line in rest:
        if line.strip() == "":
            if cur:
                paragraphs.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur:
        paragraphs.append(cur)

    footers: list[Footer] = []
    if paragraphs:
        last = paragraphs[-1]
        is_footer_block = True
        parsed: list[Footer] = []
        for line in last:
            tm = TRAILER_RE.match(line)
            if tm:
                parsed.append(Footer(tm.group("token"), tm.group("value")))
            elif line[:1] in (" ", "\t") and parsed:
                parsed[-1].value += "\n" + line.strip()
            else:
                is_footer_block = False
                break
        if is_footer_block and parsed:
            footers = parsed
            paragraphs = paragraphs[:-1]

    c.footers = footers
    c.body = "\n\n".join("\n".join(p) for p in paragraphs).strip()
    return c
