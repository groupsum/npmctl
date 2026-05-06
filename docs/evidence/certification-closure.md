# Certification Closure Evidence

This artifact records the corrective certification closure for the npmctl
package. It supersedes broad planning proof for final release certification by
splitting proof across feature families with direct tests, claims, evidence,
and governing SPEC links.

Certification policy:

- Statement and branch coverage must be 100%.
- No source module may remain uncovered.
- Independent feature families must not rely on one broad planning claim as
  final release proof.
- Compliance artifacts must be machine-readable and fail closed when missing,
  stale, or failing.
- Live NPM conformance evidence is release-blocking for the supported release
  profile.

Implemented closure surfaces:

- Coverage family: `pyproject.toml` enforces `fail_under = 100` with branch
  coverage enabled, and `packages/npmctl/tests/unit/test_certification_closure.py`
  covers public wrappers, entrypoints, branch edges, and operational helpers.
- CLI/operator family: diagnostics, environment reporting, completion,
  migration, schema, plugin listing, and compliance gate behavior are covered
  through focused unit and integration tests.
- Operational hardening family: audit, rollback, backup, drift, transaction
  reporting, and container CLI artifacts are covered by operational tests,
  workflow checks, and Dockerfile presence.
- Compliance family: compliance artifact generation now emits SBOM,
  provenance, security scan, dependency audit, and release-gate JSON artifacts;
  `npmctl compliance gate` rejects missing or failing artifacts.
- Conformance family: release publication is gated on successful live NPM E2E
  workflow evidence for the supported profile rather than optional local skips.
- Resource family: expanded resources remain covered by the desired-state
  schema, plan-output schema, and fake-NPM behavior tests.
- Plugin/extension family: runtime provider discovery, validation, diagnostic
  listing, and invalid-provider failures are covered by tests.
- Development gate family: SSOT validation, generated docs, schema validation,
  ruff, yamllint, pytest, and 100% coverage remain explicit release gates.

Verification commands:

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run yamllint .`
- `uv run pytest`
- `uv run coverage report --fail-under=100`
- `uv run ssot validate . --write-report`
- `uv run python tools/render_ssot_docs.py --check`
- `uv run python scripts/validate_schemas.py`
