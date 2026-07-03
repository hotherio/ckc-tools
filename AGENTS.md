# AGENTS.md

Entry point for AI coding agents (Cursor, Codex, Aider, Continue, Claude Code, ...) working in a
repo that uses **Conventional Knowledge Commits (CKC)**. Vendor this file into any CKC repo.

CKC is a strict superset of Conventional Commits for knowledge work: math claims and proofs, and
empirical findings. Every CKC commit is a valid Conventional Commit; it adds research types, an
epistemic `Status:` footer, and relation footers that let tooling build a dependency graph of claims.

## Writing a commit

```
<type>[~][(scope)][!]: <description>

[body]

<footers>            # git trailers: Token: value, repeatable
```

1. **One claim per commit** (one theorem, lemma, definition, or finding).
2. **Type** by profile (full lists: `ckc_lint/vocab.json`): proof — `state`, `proof`, `formalize`,
   `axiomatize`, `strengthen`, `generalize`, `weaken!`, `port`; science — `experiment`, `result`,
   `replicate`, `null`, `data`, `protocol`, `method`, `analysis`, `repro-fix`; shared — `conjecture`,
   `lit`, `review`, `refute!`, `retract!`, `expose`, `meta`. Plain `feat`/`fix`/`docs`/`chore` still
   apply to tooling and prose.
3. **`Status:`** — math: `math.conjectured`, `math.proved-informal`, `math.open`, `math.axiomatised`,
   `math.machine-checked`, `math.disproved`; sci: `sci.hypothesis`, `sci.piloted`, `sci.measured`,
   `sci.supported`, `sci.replicated`, `sci.not-replicated`, `sci.falsified`.
4. **Relation footers** (build the graph): `Depends-On`, `Assumes`, `Proves`, `Closes`, `Refutes`,
   `Disproves`, `Supersedes`, `Retracts`, `Invalidates`. Reference claims by the proof assistant's
   fully-qualified name or a `claims.toml` slug (`conjecture:<slug>`), never a commit hash.
5. **Trusted-base markers** (uppercase, set `~` too): `AXIOM:`, `OPEN:`, `ASSUMES:`, `UNREPLICATED:`.
6. **Fidelity footers** (spec v0.2.0 rule 14): `Source-Ref: <work, locus>` — the source anchor of a
   transcribed statement (theorem, equation, or page; `Paper-Ref:` is a deprecated alias, removed in
   v0.4.0); `Refutation-Attempt: <artifact>` — an attempt to refute the statement as written;
   `Protocol-Deviations: none | <log>` — as-run vs registered protocol, when a `Pre-Registration:`
   or `Protocol:` is cited; `Fidelity-Reviewed: <who/when>` — optional human sign-off.

## Rules of thumb

- A CKC commit MUST be a valid Conventional Commit; one claim per commit.
- Three honesties: **kernel-honest** (the trusted base is what the kernel reports), **status-honest**
  (the footers repeat that report literally), **transcription-honest** (the statement matches its
  source — the kernel cannot check this; the fidelity footers make it auditable).
- Never claim `math.machine-checked` while a `sorry`/`sorryAx` or non-standard axiom is present; the
  `Axioms:` footer should be the literal `#print axioms` output.
- An `axiomatize` commit (`Status: math.axiomatised`) MUST carry an `AXIOM:` footer and a
  `Source-Ref:` footer, and SHOULD carry a `Refutation-Attempt:` (the `ckc-axiom-check` hook
  rejects an axiomatised commit missing the anchor or the attempt).
- Status changes by adding a new commit, never by editing an old one.
- Negative results (counterexamples, null results, failed replications) are normal commits, never
  hidden or relabelled as a `fix`.

## Validate

```bash
pip install git+https://github.com/hotherio/ckc-tools     # provides ckc-lint
ckc-lint .git/COMMIT_EDITMSG                              # exit 0 = valid, 1 = rejected
```

## More

- Condensed spec (AI-readable): https://conventional-knowledge-commits.org/llms.txt
- Full spec, profiles, examples: https://conventional-knowledge-commits.org/
- ClaimGraph tool: https://github.com/hotherio/claimgraph · live viewer:
  https://claimgraph.conventional-knowledge-commits.org/
- **Claude Code** users get a richer skill: `/ckc:conventional-knowledge-commits` (this repo is a
  plugin; see `skills/conventional-knowledge-commits/`).
