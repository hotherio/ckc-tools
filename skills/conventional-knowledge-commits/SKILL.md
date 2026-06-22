---
name: conventional-knowledge-commits
description: >-
  Write and validate Conventional Knowledge Commits (CKC) for knowledge work. Use when committing a
  theorem, lemma, definition, conjecture, paper proof, or Lean/Rocq/Coq formalization (a closed
  `sorry`, a cited axiom, a refutation), or an empirical experiment, result, replication, or null
  result; when setting a `Status:` footer or a relation footer (`Depends-On`, `Closes`, `Proves`,
  `Refutes`, `Supersedes`); when a repo has a `.ckc.toml`, a `claims.toml`, or CKC-typed history; or
  when asked to explain CKC, validate a commit message, or build the ClaimGraph. Invoke as
  /ckc:conventional-knowledge-commits.
license: MIT
---

# Conventional Knowledge Commits

CKC is a strict superset of Conventional Commits for recording knowledge work: mathematical claims
and proofs, and empirical findings. A CKC commit is always a valid Conventional Commit; it adds
research types, an epistemic `Status:`, and structured footers (git trailers) that let tooling build
a dependency graph of claims (the ClaimGraph) and track what is conjectured, proved, assumed, open,
or refuted. Do not invent vocabulary: the authoritative lists live in `ckc_lint/vocab.json` (this
repo) and the condensed spec at https://conventional-knowledge-commits.org/llms.txt.

## When this applies

Treat a repo as CKC if any of these hold: a `.ckc.toml` or `claims.toml` exists; the history already
uses CKC types (`conjecture`, `formalize`, `experiment`, ...); or it is a math/science repo with a
Lean/Rocq/Coq/Isabelle project or a Lean Blueprint. In a CKC repo, commits that assert a claim use
the convention below. Plain Conventional Commits (`feat`, `fix`, `docs`, `chore`) remain valid for
tooling and prose, unchanged.

## Grammar

```
<type>[~][(scope)][!]: <description>

[body]

[footers]
```

- `!` (or a `BREAKING CHANGE:` footer) marks a change that invalidates dependents.
- `~` before the `:` flags a trusted-base caveat; the uppercase footer is the canonical record.
- Footers are git trailers: `Token: value`, repeatable, one relation/value per line.

## Authoring procedure

1. **One claim per commit.** A commit asserts a single theorem, lemma, definition, or finding, so the
   ClaimGraph has well-defined nodes. Split unrelated work.
2. **Pick the type** from the right profile (full lists: `ckc_lint/vocab.json`):
   - *proof*: `state`, `proof`, `formalize`, `axiomatize`, `strengthen`, `generalize`, `weaken` (`!`),
     `port`.
   - *science*: `experiment`, `result`, `replicate`, `null`, `data`, `protocol`, `method`, `analysis`,
     `repro-fix`.
   - *shared*: `conjecture`, `lit`, `review`, `refute` (usually `!`), `retract` (`!`), `expose`, `meta`.
3. **Set `Status:`** (axis 2, the epistemic state — namespaced):
   - math: `math.conjectured`, `math.proved-informal`, `math.open` (a `sorry`/`sorryAx`),
     `math.axiomatised` (rests on a cited axiom), `math.machine-checked` (clean kernel), `math.disproved`.
   - sci: `sci.hypothesis`, `sci.piloted`, `sci.measured`, `sci.supported`, `sci.replicated`,
     `sci.not-replicated`, `sci.falsified`.
4. **Add relation footers** (these build the graph, repeatable): `Depends-On`, `Assumes`, `Proves`,
   `Closes`, `Refutes`, `Disproves`, `Supersedes`, `Retracts`, `Invalidates`. Reference a claim by its
   stable id: the proof assistant's fully-qualified name (e.g. `IGL.fubini_factorization`) or a
   `claims.toml` slug written `conjecture:<slug>`. Never use a commit hash as a claim id.
5. **Add trusted-base markers** (uppercase footers, like `BREAKING CHANGE`) when the status is not
   clean: `AXIOM: <name> (<why>)`, `OPEN: <what is unproven>`, `ASSUMES: <untested assumption>`,
   `UNREPLICATED: <scope>`. If you write one, also flag `~` on the type.
6. **Add provenance** as relevant: `Lean:`/`Formal-Statement:` (the declaration id),
   `Axioms:` (the literal `#print axioms` output), `Verified-By:`, `Claim-ID:`, `Cites:`; for science,
   `Dataset:`, `Sample-Size:`, `Effect-Size:`, `CI:`, `P-Value:`, `Seed:`, `Pre-Registration:`.

## Honesty rules (do not break these)

- Never claim `Status: math.machine-checked` while a `sorry`/`sorryAx` or a non-standard axiom is
  present. A clean `Axioms:` line shows only `propext, Classical.choice, Quot.sound`. If the kernel is
  not clean, the status is `math.open` (with `OPEN:`) or `math.axiomatised` (with `AXIOM:`).
- A status advances only by adding a **new** commit, never by editing an old one (history is
  append-only; the graph reads the latest status).
- Negative results — counterexamples, null results, failed replications — are normal commits with
  their own type (`refute`, `null`, `replicate`). Never hide them or relabel them as a `fix`.
- A node's *effective* status is the minimum over its `Depends-On`/`Assumes` closure, so a clean proof
  that depends on an axiomatised lemma is effectively axiomatised. The ClaimGraph computes this; the
  commit need not restate it.

## Validate before committing

Run the validator (a drop-in superset of conventional-pre-commit; installed from this repo with
`pip install git+https://github.com/hotherio/ckc-tools`):

```bash
ckc-lint --message "$(cat .git/COMMIT_EDITMSG)"   # or: ckc-lint .git/COMMIT_EDITMSG
```

Exit 0 = valid; 1 = rejected. It checks the header, that the type and `Status:` are known, that
trusted-base/breaking tokens are uppercase, and warns on `~`/footer mismatches and honesty gaps
(e.g. `axiomatised` without an `AXIOM:` line). For a built Lean project, `ckc-axiom-check
.git/COMMIT_EDITMSG` cross-checks a `machine-checked`/`axiomatised` claim against the kernel.

Profiles are resolved from `--profile`, then `$CKC_PROFILES`, then `.ckc.toml` (`profiles = ["proof"]`),
defaulting to both. `ckc-lint --print-types` prints the active type list for a repo's config.

## See the graph

The `claimgraph` tool (https://github.com/hotherio/claimgraph) reconstructs the ClaimGraph from
history and answers what is proved vs. assumed vs. open, and what a refutation would put in question:

```bash
claimgraph status .                 # claims grouped by effective status
claimgraph affected <claim-id> .    # what falls if this claim is refuted
```

For a Lean Blueprint, `claimgraph reconcile`/`audit`/`depcheck` cross-check `\leanok`, the commit
`Status:`, and `#print axioms`. Full command reference: `references/tooling.md`.

## Reference files

- `references/tooling.md` — install + every `ckc-lint` / `ckc-axiom-check` / `claimgraph` command,
  and which need a built Lean project vs run offline.
- `examples/` — runnable example commit messages (a clean `formalize`, an `axiomatize~` with `AXIOM:`,
  a `refute!`, and a science `replicate`).
- Full spec: https://conventional-knowledge-commits.org/ · condensed: `/llms.txt` · vocabulary SoT:
  `ckc_lint/vocab.json`.
