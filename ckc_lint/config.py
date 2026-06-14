"""Resolve which CKC profiles are active for a repository.

Precedence: --profile flag, then $CKC_PROFILES, then a .ckc.toml config file (searched
upward from the working directory), then the default (both profiles). Values are
'proof', 'science', or 'both'/'all'.
"""
from __future__ import annotations

import os
from pathlib import Path

from .data import ALL_PROFILES

try:  # Python 3.11+
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore


def _split(raw) -> set[str]:
    if isinstance(raw, str):
        parts = [p.strip().lower() for p in raw.replace(",", " ").split()]
    else:  # an iterable from a config list
        parts = [str(p).strip().lower() for p in raw]
    out: set[str] = set()
    for p in parts:
        if p in ("both", "all", ""):
            out |= set(ALL_PROFILES)
        else:
            out.add(p)
    return out


def _from_config(start: Path) -> set[str] | None:
    if tomllib is None:
        return None
    for d in [start, *start.parents]:
        f = d / ".ckc.toml"
        if f.is_file():
            with f.open("rb") as fh:
                data = tomllib.load(fh)
            prof = data.get("profiles")
            if prof is None:
                prof = data.get("ckc", {}).get("profiles")
            if prof is not None:
                return _split(prof)
        if (d / ".git").exists():
            break  # stop at the repo root
    return None


def resolve_profiles(cli: str | list[str] | None = None, start_dir: str | None = None) -> set[str]:
    """Return the active profile set (a non-empty subset of ALL_PROFILES)."""
    valid = set(ALL_PROFILES)
    if cli:
        sel = _split(cli if isinstance(cli, str) else " ".join(cli))
    elif os.environ.get("CKC_PROFILES"):
        sel = _split(os.environ["CKC_PROFILES"])
    else:
        sel = _from_config(Path(start_dir or os.getcwd()).resolve())
    if not sel:
        return set(valid)  # default: both
    sel &= valid
    return sel or set(valid)  # ignore unknown tokens rather than block everything
