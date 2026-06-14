"""Load the CKC vocabulary (the single source of truth, vocab.json)."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def vocab() -> dict:
    """Return the parsed vocab.json.

    Resolution order: $CKC_VOCAB override, then the copy packaged inside ckc_lint.
    """
    override = os.environ.get("CKC_VOCAB")
    if override:
        with open(override, encoding="utf-8") as fh:
            return json.load(fh)
    with resources.files(__package__).joinpath("vocab.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def all_types() -> set[str]:
    t = vocab()["types"]
    return set(t["shared"]) | set(t["proof"]) | set(t["science"]) | set(t["conventional"])


def profile_of(commit_type: str) -> str | None:
    """proof | science | shared | conventional, or None if unknown."""
    t = vocab()["types"]
    for name in ("proof", "science", "shared", "conventional"):
        if commit_type in t[name]:
            return name
    return None


def all_statuses() -> set[str]:
    s = vocab()["status"]
    return set(s["math"]) | set(s["sci"])


def trusted_base_tokens() -> set[str]:
    return set(vocab()["trusted_base_tokens"])


def breaking_tokens() -> set[str]:
    return set(vocab()["breaking_tokens"])


def relation_tokens() -> set[str]:
    return set(vocab()["relation_tokens"])
