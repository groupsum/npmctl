# Expanded Feature Scope Evidence

This artifact records the implementation verification bundle for the expanded
npmctl feature scope.

This is retained as historical planning evidence. Final certification proof is
closed through `docs/evidence/certification-closure.md` and the feature-family
claim, test, and evidence rows linked directly in the SSOT registry.

Implemented surfaces include expanded desired-state resources, operator
diagnostic commands, config-file loading, completion output, JSON version
output, drift reporting, audit-log reading, operational apply artifacts,
compliance artifact generation, conformance documentation, plugin contracts,
real-NPM CI coverage artifact wiring, and a raised coverage threshold.

Verification:

- `packages/npmctl/tests/unit/test_expanded_features.py`
- `.github/workflows/live-npm-gate.yml`
- `.github/actions/npmctl-real-npm-e2e/action.yml`
- `schemas/npmctl/desired-state.v1.schema.json`
- `schemas/npmctl/plan-output.v1.schema.json`
