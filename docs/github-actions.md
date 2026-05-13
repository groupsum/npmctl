# GitHub Actions

The repository includes local composite actions and gated workflows.

## Local actions

- `.github/actions/setup-uv-python`
- `.github/actions/npmctl-check`
- `.github/actions/npmctl-schema-gate`
- `.github/actions/npmctl-ssot-gate`
- `.github/actions/npmctl-real-npm-e2e`
- `.github/actions/npmctl-release-build`

## Workflows

- `CI`: lint, format, YAML lint, pytest, schema gate.
- `Docs and SSOT`: runs after CI succeeds.
- `Python Matrix`: runs pytest on Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- `Live NPM Gate`: starts Nginx Proxy Manager in Docker and runs opt-in pytest E2E.
- `Release`: dispatches CI, Docs/SSOT, `Python Matrix`, and `Live NPM Gate`, waits for all to pass on the release ref, then builds. Dispatch checkboxes control GitHub Release creation and PyPI publishing.

Each workflow uses concurrency groups to avoid overlapping mutable runs.
