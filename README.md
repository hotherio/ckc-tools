# ckc-tools

Git hooks and configs for [Conventional Knowledge Commits (CKC)](https://hotherio.github.io/conventional-knowledge-commits/).

CKC is a strict superset of [Conventional Commits](https://www.conventionalcommits.org/). These
tools validate CKC commit messages and are built to **compose with existing Conventional Commits
tooling, not collide with it**.

## What's here

- **`ckc-lint`** — a `commit-msg` validator (Python, no Node). Checks that a message is a valid
  Conventional Commit and follows CKC: a known type, a known `Status:` value, uppercase trusted-base
  markers, `~` consistency, well-formed relation footers. It accepts plain Conventional Commits
  unchanged.
- **`ckc-axiom-check`** — an opt-in honesty hook for the proof profile. If a commit claims
  `Status: math.machine-checked`, it cross-checks the named `Lean:` declarations against the kernel
  via the lean-math `axiom-report` and rejects the commit if the kernel disagrees.
- **`commitlint-config-ckc`** — a [commitlint](https://commitlint.js.org/) shareable config for the
  JavaScript world; it widens `type-enum` to the CKC vocabulary.

The vocabulary lives in one place, `ckc_lint/vocab.json`, shared by the Python validator and the
commitlint config.

## The collision, and how this avoids it

A strict Conventional Commits validator only allows a fixed list of types, so it rejects CKC types
(`formalize`, `experiment`, ...). Because CKC is a *superset*, a CKC validator already accepts every
plain Conventional Commit (`feat`, `fix`, `docs`, `chore`). The rule is simple: **never run two
validators with disjoint type lists.**

## Install (pre-commit framework)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/hotherio/ckc-tools
    rev: v0.1.0
    hooks:
      - id: ckc
      # opt-in proof honesty check (needs Lean + axiom-report):
      # - id: ckc-axiom-check
```

```bash
pre-commit install --hook-type commit-msg
```

If you already use [`conventional-pre-commit`](https://github.com/compilerla/conventional-pre-commit),
**replace it with `ckc`** (a superset that still accepts plain Conventional Commits), or keep it and
pass the CKC types in its `args:` so it stops rejecting them. Do not run both with different type
lists.

## Install (commitlint)

```js
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional', 'commitlint-config-ckc'],
};
```

`commitlint-config-ckc` extends `config-conventional` and only widens `type-enum`. Do not add a
second config that re-narrows the type list. The deeper CKC checks live in `ckc-lint`.

## A mixed repository (paper and proofs together)

Use the CKC validator only. It accepts both plain Conventional Commits for tooling and prose
(`chore`, `docs`, `feat`) and CKC commits for the work (`conjecture`, `formalize`, `experiment`).
There is nothing to reconcile.

## The honesty hook

`ckc-axiom-check` is opt-in. It only acts on a commit that claims `math.machine-checked` or
`math.axiomatised` and names `Lean:` declarations. It runs `axiom-report` (from the lean-math plugin;
set `$CKC_AXIOM_REPORT` to its path, and `$CKC_PROJECT` to the Lean project dir if it is not the
working directory). It rejects only a genuine contradiction (the kernel reports a `sorryAx` or a
cited axiom while the commit claims `machine-checked`). If it cannot determine a declaration's status
it skips, unless you pass `--require`. This extends the lean-math working-tree honesty gate into the
commit log.

## Use without a hook framework

```bash
pip install git+https://github.com/hotherio/ckc-tools
ckc-lint .git/COMMIT_EDITMSG          # or: ckc-lint --message "formalize(x): ..."
```

`ckc-lint` is a standard `commit-msg` hook: it takes the message file as its argument and exits
non-zero to block the commit.

## Develop and test

```bash
python3 tests/run.py            # the validator test suite, no dependencies
```

There is no CI (the organization disables GitHub Actions); run the suite locally. The pre-commit hook
is pulled from this repository by tag, so it needs no package registry.

## License

MIT (see [LICENSE](LICENSE)). The CKC specification itself is CC BY 4.0.
