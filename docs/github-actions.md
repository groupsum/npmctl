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
- `Release`: dispatches CI, Docs/SSOT, `Python Matrix`, and `Live NPM Gate`, waits for all to pass on the release ref, then builds. When PyPI publishing is enabled, PyPI upload must succeed before the GitHub Release is created or updated. Dispatch checkboxes control GitHub Release creation and PyPI publishing.

Each workflow uses concurrency groups to avoid overlapping mutable runs.

## PyPI Trusted Publishing

The `Release` workflow publishes from `.github/workflows/release.yml` with
`id-token: write` and the `pypi` GitHub environment. PyPI trusted publisher
configuration is project-scoped, so every package published from this workspace
needs a matching PyPI publisher entry:

| PyPI project | GitHub owner | GitHub repository | Workflow filename | Environment |
| --- | --- | --- | --- | --- |
| `npmctl` | `groupsum` | `npmctl` | `release.yml` | `pypi` |
| `npmctl-namecheap` | `groupsum` | `npmctl` | `release.yml` | `pypi` |
| `npmctl-cloudflare` | `groupsum` | `npmctl` | `release.yml` | `pypi` |
| `npmctl-digitalocean` | `groupsum` | `npmctl` | `release.yml` | `pypi` |
| `npmctl-godaddy` | `groupsum` | `npmctl` | `release.yml` | `pypi` |
| `npmctl-route53` | `groupsum` | `npmctl` | `release.yml` | `pypi` |

The publish job first uses `pypa/gh-action-pypi-publish@release/v1` without
credentials, which is the trusted publishing path. The token fallback is only
for projects that have not yet been configured in PyPI. When PyPI publishing is
enabled, the GitHub Release step runs after PyPI succeeds so failed package
publication does not leave a new GitHub-only release.
