# npmctl

[![CI](https://github.com/example/npmctl/actions/workflows/ci.yml/badge.svg)](https://github.com/example/npmctl/actions/workflows/ci.yml)
[![Real NPM E2E](https://github.com/example/npmctl/actions/workflows/e2e-npm.yml/badge.svg)](https://github.com/example/npmctl/actions/workflows/e2e-npm.yml)
[![PyPI](https://img.shields.io/pypi/v/npmctl.svg)](https://pypi.org/project/npmctl/)

`npmctl` is an owner-scoped GitOps controller for Nginx Proxy Manager. It provides `validate`, `migrate`, `schema`, `plan`, `apply`, and `adopt` commands for proxy hosts, SSL certificates, and access lists.

## Core safety model

- All managed resources require `meta.managed_by: npmctl`, `meta.owner`, and `meta.resource_id`.
- A workload can create, update, delete, or adopt only resources inside its owner scope.
- Foreign-owned resources are immutable to the current owner.
- Manual/unmanaged resources cannot be mutated unless `npmctl adopt` is explicitly invoked.
- Prune/delete is never implicit; use `--prune-owned`.
- API operations are schema-gated and fail closed when the NPM OpenAPI schema does not expose the required endpoint.

## CLI quickstart

```bash
uv run npmctl validate examples/desired-state
uv run npmctl schema capabilities --schema schemas/npm/2.10.4/openapi.json
uv run npmctl plan examples/desired-state --owner workload-a
uv run npmctl apply examples/desired-state --owner workload-a
uv run npmctl adopt examples/desired-state --owner workload-a
```

## Desired state

```yaml
apiVersion: npmctl.io/v1
schemaVersion: 1
proxy_hosts:
  - domain_names: [app.example.com]
    forward_host: app
    forward_port: 3000
    meta:
      managed_by: npmctl
      owner: workload-a
      resource_id: proxy.app
```

See `docs/` for architecture, CLI, schema migrations, GitHub Actions, SSL certificates, access lists, and adoption semantics.
