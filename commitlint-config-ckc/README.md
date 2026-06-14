# commitlint-config-ckc

A [commitlint](https://commitlint.js.org/) shareable config for
[Conventional Knowledge Commits](https://hotherio.github.io/conventional-knowledge-commits/).

It extends `@commitlint/config-conventional` and widens the `type-enum` rule to the CKC vocabulary,
so commitlint accepts both plain Conventional Commits and CKC commits in the same repository.

## Use

```js
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional', 'commitlint-config-ckc'],
};
```

The deeper CKC checks (status values, trusted-base markers, the `~` flag, the proof honesty check)
live in the `ckc-lint` / `ckc-axiom-check` hooks in the same repository; this config only handles the
type list, which is the part that otherwise collides with a strict Conventional Commits setup.

The type list comes from `ckc_lint/vocab.json`, the single source of truth shared with the Python
validator.
