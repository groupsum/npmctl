# npmctl

`npmctl` is the Python package and console script for owner-scoped Nginx Proxy Manager automation. It validates desired-state YAML, computes safe plans, applies clean changes, and adopts unmanaged resources only when explicitly requested.

## Install

Use `pipx` for an isolated CLI install:

```bash
pipx install npmctl
npmctl --version
```

Use `uv` if you manage tools with uv:

```bash
uv tool install npmctl
npmctl --help
```

Use `pip` inside an existing virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install npmctl
npmctl --help
```

PowerShell activation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install npmctl
npmctl --help
```

## Configure NPM

Set Nginx Proxy Manager API credentials as environment variables:

```bash
export NPM_BASE_URL=http://127.0.0.1:81/api
export NPM_IDENTITY=admin@example.com
export NPM_SECRET=changeme
```

Or pass them directly:

```bash
npmctl --base-url http://127.0.0.1:81/api --identity admin@example.com --secret changeme health
```

## Desired State

Every managed resource needs npmctl ownership metadata:

```yaml
apiVersion: npmctl.com/v1
schemaVersion: 1
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

References use `resource_id` values:

```yaml
apiVersion: npmctl.com/v1
schemaVersion: 1
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
    forward_host: app
    forward_port: 3000
    certificate_ref: cert.wildcard-example
    access_list_ref: acl.private-admins
    ssl_forced: 1
    allow_websocket_upgrade: 1
    caching_enabled: 1
    block_exploits: 1
    meta:
      managed_by: npmctl
      owner: workload-a
      resource_id: proxy.app
```

## Commands

Validate files without calling the NPM API:

```bash
npmctl validate ./desired-state
npmctl --output json validate ./desired-state
```

Check or write desired-state schema migrations:

```bash
npmctl migrate ./desired-state --check
npmctl migrate ./desired-state --write
```

Check the target NPM API:

```bash
npmctl health
npmctl schema fetch --write npm-openapi.json
npmctl schema capabilities
npmctl schema check
```

Plan and apply by owner:

```bash
npmctl plan ./desired-state --owner workload-a
npmctl apply ./desired-state --owner workload-a
```

Preview apply without mutation:

```bash
npmctl apply ./desired-state --owner workload-a --dry-run
```

Prune owned resources absent from desired state:

```bash
npmctl apply ./desired-state --owner workload-a --prune-owned
```

Adopt unmanaged matching resources:

```bash
npmctl adopt ./desired-state --owner workload-a
npmctl adopt ./desired-state --owner workload-a --allow-field-drift
```

## Exit Codes

- `0`: success
- `1`: plan conflict
- `2`: usage, validation, or migration error
- `3`: API error
- `4`: endpoint capability error

## More Documentation

The source repository includes detailed docs and examples:

- https://github.com/groupsum/npmctl
- https://github.com/groupsum/npmctl/tree/master/examples/desired-state
- https://github.com/groupsum/npmctl/tree/master/docs
