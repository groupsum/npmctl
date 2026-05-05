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
- `Real NPM E2E`: starts Nginx Proxy Manager in Docker and runs opt-in pytest E2E after CI succeeds.
- `Release`: builds after Real NPM E2E succeeds.

Each workflow uses concurrency groups to avoid overlapping mutable runs.
