<h1 align="center">npmctl</h1>

<p align="center"><strong>Owner-scoped GitOps for Nginx Proxy Manager</strong></p>

<p align="center">
  Validate desired-state YAML, plan safe owner-scoped changes, apply clean reconciles, and adopt existing NPM resources only when you ask for it.
</p>

<p align="center">
  <a href="https://pypi.org/project/npmctl/"><img src="https://img.shields.io/pypi/v/npmctl.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/npmctl/"><img src="https://img.shields.io/pypi/pyversions/npmctl.svg" alt="Python versions"></a>
  <a href="https://github.com/groupsum/npmctl/actions/workflows/ci.yml"><img src="https://github.com/groupsum/npmctl/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
  <a href="https://github.com/groupsum/npmctl/actions/workflows/python-matrix.yml"><img src="https://github.com/groupsum/npmctl/actions/workflows/python-matrix.yml/badge.svg?branch=master" alt="Python Matrix"></a>
  <a href="https://github.com/groupsum/npmctl/actions/workflows/live-npm-gate.yml"><img src="https://github.com/groupsum/npmctl/actions/workflows/live-npm-gate.yml/badge.svg?branch=master" alt="Live NPM Gate"></a>
  <a href="https://github.com/groupsum/npmctl/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License"></a>
</p>

<p align="center">
  <a href="https://hits.sh/github.com/groupsum/npmctl/blob/master/README.md/"><img src="https://hits.sh/github.com/groupsum/npmctl/blob/master/README.md.svg?label=npmctl%20repository%20hits" alt="npmctl repository hits"></a>
  <a href="https://pepy.tech/projects/npmctl"><img src="https://static.pepy.tech/badge/npmctl" alt="npmctl downloads"></a>
  <a href="https://pepy.tech/projects/npmctl-namecheap"><img src="https://static.pepy.tech/badge/npmctl-namecheap" alt="npmctl-namecheap downloads"></a>
</p>

`npmctl` is an owner-scoped GitOps controller for Nginx Proxy Manager. It validates desired-state YAML, plans safe changes against a live NPM API, applies clean plans, and adopts unmanaged resources only when explicitly requested.

## FAQ

### What is npmctl?

**Answer:** `npmctl` is a declarative controller for Nginx Proxy Manager that turns YAML desired state into safe owner-scoped plans, applies clean reconciles, and blocks unsafe mutations before they hit production.

### What problem does npmctl solve?

**Answer:** `npmctl` replaces manual NPM clicking and brittle API scripts with repeatable plan/apply/adopt workflows for proxy hosts, certificates, access lists, and related resources.

### Does npmctl modify resources it does not own?

**Answer:** No. `npmctl` treats NPM resources as owner-scoped, refuses to mutate foreign-owned resources, and requires explicit adoption before unmanaged resources come under npmctl control.

### How does npmctl handle certificate issuance and rotation?

**Answer:** `npmctl` treats certificates as declarative resources in desired state. Issuance happens when a desired certificate must be created, and rotation is controlled through reconcile policy rather than implicit side effects during unrelated repair work.

### Can npmctl adopt existing manual resources safely?

**Answer:** Yes. `npmctl adopt` is the explicit path for attaching npmctl ownership metadata to compatible unmanaged resources so later plans and applies remain conservative and traceable.

It manages:

- Proxy hosts
- SSL certificates
- Access lists
- Redirection hosts
- Dead hosts
- Streams
- Users
- Settings
- Provider-backed DNS records

It also provides read-only audit log reporting, operator diagnostics, compliance
artifact generation, and plugin contracts for future custom resource and
certificate and DNS providers.

## Safety Model

- Every managed resource must carry `meta.managed_by: npmctl`, `meta.owner`, and `meta.resource_id`.
- `--owner` limits planning and mutation to one owner scope.
- Foreign-owned resources are immutable to the current owner.
- Unmanaged resources are not changed by `plan` or `apply`; use `adopt` to attach npmctl metadata.
- Deletes are opt-in with `--prune-owned`.
- API operations are gated by the NPM OpenAPI schema and fail closed when a required endpoint is unavailable.

## Requirements

- Python `3.10`, `3.11`, `3.12`, `3.13`, or `3.14`
- Access to a Nginx Proxy Manager API, usually `http://host:81/api`
- NPM admin credentials or an account with permissions for the resources you want to manage
- Optional for local development: Docker and Docker Compose

## Install

Install the published CLI with `pipx`:

```bash
pipx install npmctl
npmctl --version
npmctl --help
```

Install with `uv` as a tool:

```bash
uv tool install npmctl
npmctl --help
```

Install from a local checkout:

```bash
git clone https://github.com/groupsum/npmctl.git
cd npmctl
uv sync
uv run npmctl --help
```

Run directly from the workspace while developing:

```bash
uv run npmctl validate examples/desired-state
uv run pytest
```

## Configure API Access

You can pass API credentials on every command:

```bash
npmctl --base-url http://127.0.0.1:81/api --identity admin@example.com --secret changeme health
```

For regular use, set environment variables:

```bash
export NPM_BASE_URL=http://127.0.0.1:81/api
export NPM_IDENTITY=admin@example.com
export NPM_SECRET=changeme
export NPM_TIMEOUT_S=15
```

PowerShell:

```powershell
$env:NPM_BASE_URL = "http://127.0.0.1:81/api"
$env:NPM_IDENTITY = "admin@example.com"
$env:NPM_SECRET = "changeme"
$env:NPM_TIMEOUT_S = "15"
```

Then verify connectivity:

```bash
npmctl health
```

## Local NPM Stack

The repo includes a SQLite-backed NPM stack for local testing:

```bash
docker compose -f deploy/npm/docker-compose.yml up -d
export NPM_BASE_URL=http://127.0.0.1:81/api
export NPM_IDENTITY=admin@example.com
export NPM_SECRET=changeme
npmctl health
```

For details, see [deploy/npm/README.md](deploy/npm/README.md).

## Desired State

A minimal proxy host:

```yaml
apiVersion: npmctl.com/v1
schemaVersion: 2
proxy_hosts:
  - domain_names: [app.example.com]
    forward_scheme: http
    forward_host: app
    forward_port: 3000
    meta:
      managed_by: npmctl
      owner: workload-a
      resource_id: proxy.app
```

A proxy host with certificate and access-list references:

```yaml
apiVersion: npmctl.com/v1
schemaVersion: 2
certificates:
  - name: wildcard-example
    domain_names: ["*.example.com", example.com]
    certificate_type: letsencrypt
    api_payload:
      provider: letsencrypt
    meta:
      managed_by: npmctl
      owner: workload-a
      resource_id: cert.wildcard-example
access_lists:
  - name: private-admins
    api_payload:
      satisfy_any: 0
      items: []
      clients: []
    meta:
      managed_by: npmctl
      owner: workload-a
      resource_id: acl.private-admins
proxy_hosts:
  - domain_names: [app.example.com]
    forward_scheme: http
    forward_host: app
    forward_port: 3000
    certificate_ref: cert.wildcard-example
    access_list_ref: acl.private-admins
    ssl_forced: 1
    http2_support: 1
    allow_websocket_upgrade: 1
    caching_enabled: 1
    block_exploits: 1
    meta:
      managed_by: npmctl
      owner: workload-a
      resource_id: proxy.app
```

More examples are in [examples/desired-state](examples/desired-state).

## Usage

Validate desired state without calling NPM:

```bash
npmctl validate examples/desired-state
npmctl --output json validate examples/desired-state
```

Check whether files need schema migration:

```bash
npmctl migrate examples/desired-state --check
npmctl migrate examples/desired-state --write
```

Fetch the live NPM OpenAPI schema:

```bash
npmctl schema fetch --write schemas/npm/live-openapi.json
```

Inspect endpoint capabilities from a schema file or from the live API:

```bash
npmctl schema capabilities --schema schemas/npm/2.10.4/openapi.json
npmctl schema capabilities
npmctl schema check
```

Plan owner-scoped changes:

```bash
npmctl plan examples/desired-state --owner workload-a
npmctl --output json plan examples/desired-state --owner workload-a
```

Apply a clean plan:

```bash
npmctl apply examples/desired-state --owner workload-a
```

Preview the apply path without mutation:

```bash
npmctl apply examples/desired-state --owner workload-a --dry-run
```

Delete owned resources that are no longer present in desired state:

```bash
npmctl apply examples/desired-state --owner workload-a --prune-owned
```

Adopt unmanaged matching resources by writing npmctl metadata:

```bash
npmctl adopt examples/desired-state --owner workload-a
```

Strict adoption requires the unmanaged resource fields to match desired state. To allow field drift while attaching metadata:

```bash
npmctl adopt examples/desired-state --owner workload-a --allow-field-drift
```

## Operational Flow

1. Author YAML with explicit `meta.owner` and `meta.resource_id`.
2. Run `npmctl validate`.
3. Run `npmctl schema check` against the target NPM instance.
4. Run `npmctl plan --owner <owner>`.
5. Review creates, updates, deletes, adopts, noops, and conflicts.
6. Run `npmctl apply --owner <owner>` only when the plan is clean.
7. Use `--prune-owned` only when absent owned resources should be deleted.

## Exit Codes

- `0`: success
- `1`: plan conflict
- `2`: usage, validation, or migration error
- `3`: API error
- `4`: endpoint capability error

## Development

Run the normal local checks:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build --package npmctl
```

Run real NPM E2E tests against the bundled CI stack:

```bash
docker compose -f deploy/npm/compose.ci.yml up -d
export NPMCTL_REAL_NPM=1
export NPM_BASE_URL=http://127.0.0.1:8181/api
export NPM_IDENTITY=admin@example.com
export NPM_SECRET=changeme
uv run pytest --no-cov -m npm packages/npmctl/tests/e2e
docker compose -f deploy/npm/compose.ci.yml down
```

## Documentation

- [CLI](docs/cli.md)
- [Desired state](docs/desired-state.md)
- [Owner-scoped reconciliation](docs/owner-scoped-reconcile.md)
- [Schema migrations](docs/schema-migrations.md)
- [NPM API compatibility](docs/npm-api-compatibility.md)
- [SSL certificates](docs/ssl-certificates.md)
- [Access lists](docs/access-lists.md)
- [DNS records](docs/dns.md)
- [Namecheap DNS extension](docs/namecheap.md)
- [Adoption](docs/adoption.md)
- [GitHub Actions](docs/github-actions.md)
