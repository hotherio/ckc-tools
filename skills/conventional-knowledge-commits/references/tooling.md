# CKC tooling command reference

Three tools. `ckc-lint` and `claimgraph` run offline; the Lean-grounded checks need a built project.

## ckc-lint (validate a commit message)

Install: `pip install git+https://github.com/hotherio/ckc-tools` (Python 3.9+). Provides `ckc-lint`
and `ckc-axiom-check`.

```bash
ckc-lint .git/COMMIT_EDITMSG          # validate a commit-msg file
ckc-lint --message "feat: add x"      # validate inline text
ckc-lint --print-types                # the active type list (both profiles)
ckc-lint --print-types --profile proof
```

Useful flags: `--profile {proof|science}` (repeatable), `--strict` (reject fixup!/squash! + warnings
become errors), `--force-scope`, `--scopes "a,b"`, `--quiet`. Exit 0 valid, 1 rejected, 2 usage.

Profile resolution: `--profile` → `$CKC_PROFILES` → `.ckc.toml` (`profiles = ["proof"]`) → both.

Checks: header shape `type[~][(scope)][!]: desc`; type ∈ vocabulary; `Status:` ∈ known `math.*`/`sci.*`;
trusted-base tokens (`AXIOM`/`OPEN`/`ASSUMES`/`UNREPLICATED`) and breaking tokens uppercase; warnings
for `~`/footer mismatch and honesty gaps (`axiomatised` w/o `AXIOM:`, `open` w/o `OPEN:`,
`machine-checked` w/o `Axioms:`).

Hook (pre-commit framework):
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/hotherio/ckc-tools
    rev: v0.1.3
    hooks: [ { id: ckc }, { id: ckc-axiom-check } ]   # second is optional
```
`pre-commit install --hook-type commit-msg`. commitlint users: extend `commitlint-config-ckc`.

## ckc-axiom-check (proof honesty, needs Lean)

```bash
ckc-axiom-check .git/COMMIT_EDITMSG --project lean/        # cross-check vs the kernel
ckc-axiom-check .git/COMMIT_EDITMSG --require              # fail if axiom-report unavailable
```
Acts only on commits claiming `Status: math.machine-checked` or `math.axiomatised` with a `Lean:` /
`Formal-Statement:` footer. Needs Lean + a built project + `axiom-report` on PATH (or
`$CKC_AXIOM_REPORT`). Exit 0 honest/skipped, 1 dishonest.

## claimgraph (build & query the ClaimGraph)

Install: `pip install git+https://github.com/hotherio/claimgraph.git` (Python 3.13+; pulls in
ckc-lint). Subcommands (all take `[REPO]`, `--claims claims.toml`, `--from-fixture FILE`):

| Command | Purpose | Needs Lean? |
|---|---|---|
| `claimgraph build . -o graph.json` | reconstruct the graph → JSON | no |
| `claimgraph status .` | claims grouped by effective status | no |
| `claimgraph affected <id> .` | what falls if `<id>` is refuted | no |
| `claimgraph effective <id> .` | a claim's effective status + weakest dependency | no |
| `claimgraph blueprint content.tex --project lean/` | import a Lean Blueprint, grounded to the kernel | yes (or `--axioms FILE`) |
| `claimgraph reconcile content.tex . --project lean/` | reconcile blueprint `\leanok` vs commit `Status:` vs `#print axioms` | yes (or `--axioms`) |
| `claimgraph audit content.tex --repo . --project lean/` | honesty gate; exit 1 on a kernel-refuted claim (`--strict` adds coverage gaps) | yes (or `--axioms`) |
| `claimgraph depcheck content.tex . --project lean/ --populate --strict` | ground `Depends-On` edges against Lean's real dependency graph | yes (or `--lean-deps FILE`) |

Offline grounding: pass `--axioms FILE` (saved `axiom-report` output) or `--lean-deps FILE` instead of
`--project`, so blueprint/reconcile/audit/depcheck run without a build.

## vocabulary (do not hardcode)

`ckc_lint/vocab.json` is the single source of truth for types, `Status:` values, relation tokens, and
provenance tokens, shared by the Python validator and the commitlint config. Override path with
`$CKC_VOCAB`. The condensed spec at https://conventional-knowledge-commits.org/llms.txt mirrors it in
prose.
