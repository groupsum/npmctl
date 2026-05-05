# Repository agent guidance

- Use uv for all Python dependency and command execution.
- Use pytest for tests.
- Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run yamllint .`, and `uv run pytest` before completion.
- NPM resources are owner-scoped. Never mutate foreign-owned resources.
- Adoption must be explicit. Delete/prune must be explicit and owner-scoped.
- Update SSOT, docs, schemas, and tests when behavior changes.
