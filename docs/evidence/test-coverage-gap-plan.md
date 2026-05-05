# Test Coverage Gap Implementation

Status: passed

This evidence row records the implemented coverage for the test gap inventory.
Each gap is represented by an SSOT feature row and an executable test row in
`.ssot/registry.json`.

Verification commands:

- `uv run --frozen pytest`
- `uv run --frozen pytest --no-cov -m npm packages/npmctl/tests/e2e`
- `uv run --frozen ruff check .`

NPM 2.10.4 omits some implemented endpoints from `/schema`, so the live E2E
suite also verifies the compatibility capability overlay against a real NPM
container.
