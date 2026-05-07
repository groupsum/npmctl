# Real NPM E2E evidence

Covered by pytest under `packages/npmctl/tests/e2e` and `.github/workflows/live-npm-gate.yml`.

Status: passed

Verification command:

- `NPMCTL_REAL_NPM=1 NPM_BASE_URL=http://127.0.0.1:18181/api NPM_IDENTITY=admin@example.com NPM_SECRET=changeme uv run pytest --no-cov -m npm packages/npmctl/tests/e2e`

Result:

- `7 passed`
