// commitlint-config-ckc — a shareable commitlint config for Conventional Knowledge Commits.
//
// It extends @commitlint/config-conventional and widens `type-enum` to the CKC union, so a
// commitlint setup accepts both plain Conventional Commits and CKC commits. This is the piece
// that prevents a strict CC validator from rejecting CKC types (formalize, experiment, ...).
//
// Usage in commitlint.config.js:
//   module.exports = { extends: ['@commitlint/config-conventional', 'commitlint-config-ckc'] };
//
// The vocabulary is read from the single source of truth, ckc_lint/vocab.json.

const vocab = require('../ckc_lint/vocab.json');
const t = vocab.types;
const types = [...t.conventional, ...t.shared, ...t.proof, ...t.science];

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', types],
  },
};
