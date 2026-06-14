# ckc-tools

Git hooks and configs for [Conventional Knowledge Commits (CKC)](https://hotherio.github.io/conventional-knowledge-commits/).

CKC is a strict superset of [Conventional Commits](https://www.conventionalcommits.org/). These
tools validate CKC commit messages and are built to **run alongside existing Conventional Commits
tooling, not replace it**.

## What's here

- **`ckc-lint`** — a `commit-msg` validator (Python, no Node). It is a **drop-in superset of
  [`conventional-pre-commit`](https://github.com/compilerla/conventional-pre-commit)**: the same CLI
  (positional types, `--strict`, `--force-scope`, `--scopes`, `--no-color`, `--verbose`, exit codes
  0/1, `fixup!`/merge commits pass unless `--strict`). On top of that it allows the CKC vocabulary by
  default and adds the CKC checks (known `Status:` value, uppercase trusted-base markers, `~`
  consistency, well-formed relation footers).
- **`ckc-axiom-check`** — an opt-in honesty hook for the proof profile. If a commit claims
  `Status: math.machine-checked`, it cross-checks the named `Lean:` declarations against the kernel
  via the lean-math `axiom-report` and rejects the commit if the kernel disagrees.
- **`commitlint-config-ckc`** — a [commitlint](https://commitlint.js.org/) shareable config that
  widens `type-enum` to the CKC vocabulary.

The vocabulary lives in one place, `ckc_lint/vocab.json`, shared by the Python validator and the
commitlint config.

## Profiles

A repository chooses which profiles are active: `proof`, `science`, or both (the default). With one
profile active, a type from the other profile is rejected (a science-only repo rejects `formalize`;
a proof-only repo rejects `experiment`). Shared types (`conjecture`, `refute`, ...) and plain
Conventional Commits types always pass.

Set it in any of these (first wins): the `--profile` flag, `$CKC_PROFILES`, or a `.ckc.toml` at the
repo root:

```toml
# .ckc.toml
profiles = ["proof"]   # or ["science"], or ["proof", "science"]
```

## pre-commit framework

For a repository with no existing Conventional Commits hook, `ckc` alone validates both Conventional
Commits and CKC:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/hotherio/ckc-tools
    rev: v0.1.3
    hooks:
      - id: ckc
        # args: [--profile, proof]      # optional; omit for both profiles
      # opt-in proof honesty check (needs Lean + axiom-report):
      # - id: ckc-axiom-check
```

```bash
pre-commit install --hook-type commit-msg
```

The hook id `ckc` is also available under the alias `conventional-knowledge-pre-commit`, named to
parallel `conventional-pre-commit`. The two ids run the same validator; use whichever you prefer.

### Keeping `conventional-pre-commit`

You do **not** have to remove [`conventional-pre-commit`](https://github.com/compilerla/conventional-pre-commit).
Keep it and run `ckc` next to it. The only adjustment is to widen `conventional-pre-commit`'s allowed
types so it stops rejecting CKC types; `ckc` then adds the CKC-specific checks.

Generate the type list for the active profiles:

```bash
ckc-lint --print-types                 # both profiles
ckc-lint --print-types --profile proof # one profile
```

Paste it into `conventional-pre-commit`'s `args` (the list `ckc-lint` prints is ready-to-use YAML):

```yaml
repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, build, chore, ci, docs, perf, refactor, revert, style, test, conjecture, lit, review, refute, retract, expose, meta, state, proof, formalize, axiomatize, strengthen, generalize, weaken, port, experiment, result, replicate, null, data, protocol, method, analysis, repro-fix]
  - repo: https://github.com/hotherio/ckc-tools
    rev: v0.1.3
    hooks:
      - id: ckc
```

Both hooks run on `commit-msg`; neither is replaced.

### Migrating to `ckc` only

Because `ckc` accepts the same interface as `conventional-pre-commit`, you can drop
`conventional-pre-commit` and keep your existing `args`. Change the `repo` and `id`; everything else
carries over:

```yaml
# before
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v3.6.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
      args: [--strict, --scopes, "api,client"]

# after — same args, now also allows CKC types and runs the CKC checks
- repo: https://github.com/hotherio/ckc-tools
  rev: v0.1.3
  hooks:
    - id: ckc
      stages: [commit-msg]
      args: [--strict, --scopes, "api,client"]
```

If your old `args` pinned an explicit type list, `ckc` honours it exactly (it restricts to those
types). Drop the list to allow the full CKC vocabulary for the active profiles.

## lefthook

```yaml
# lefthook.yml
commit-msg:
  commands:
    ckc:
      run: ckc-lint {1}
      # run: ckc-lint --profile proof {1}
```

`lefthook` passes the commit message file as `{1}`. Install `ckc-lint` first
(`pip install git+https://github.com/hotherio/ckc-tools`), then `lefthook install`.

## commitlint

```js
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional', 'commitlint-config-ckc'],
};
```

`commitlint-config-ckc` extends `config-conventional` and only widens the type list, so it runs
alongside a conventional setup rather than replacing it. The deeper CKC checks live in `ckc-lint`.

## A mixed repository (paper and proofs together)

Use `ckc` (with both profiles, the default). It accepts plain Conventional Commits for tooling and
prose (`chore`, `docs`, `feat`) and CKC commits for the work (`conjecture`, `formalize`,
`experiment`). There is nothing to reconcile.

## The honesty hook

`ckc-axiom-check` is opt-in and proof-only. It acts only on a commit that claims
`math.machine-checked` or `math.axiomatised` and names `Lean:` declarations. It runs `axiom-report`
(from the lean-math plugin; set `$CKC_AXIOM_REPORT` to its path, and `$CKC_PROJECT` to the Lean
project dir if it is not the working directory). It rejects only a genuine contradiction (the kernel
reports a `sorryAx` or a cited axiom while the commit claims `machine-checked`); if it cannot
determine a declaration's status it skips, unless you pass `--require`.

## Without a hook framework

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
