"""ckc_lint: validate commit messages against Conventional Knowledge Commits (CKC).

CKC is a strict superset of Conventional Commits, so this validator accepts every plain
Conventional Commit and additionally checks the CKC vocabulary (types, statuses, trusted-base
markers, relation footers). See https://hotherio.github.io/conventional-knowledge-commits/.
"""

__version__ = "0.1.3"
