<h1 align="center">npmctl-godaddy</h1>

<p align="center"><strong>GoDaddy DNS provider plugin for npmctl</strong></p>

<p align="center">
  Extend <code>npmctl</code> with GoDaddy-backed DNS record management for declarative workflows, provider discovery, and DNS-aware automation.
</p>

<p align="center">
  <a href="https://pypi.org/project/npmctl-godaddy/"><img src="https://img.shields.io/pypi/v/npmctl-godaddy.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/npmctl-godaddy/"><img src="https://img.shields.io/pypi/pyversions/npmctl-godaddy.svg" alt="Python versions"></a>
  <a href="https://github.com/groupsum/npmctl/actions/workflows/ci.yml"><img src="https://github.com/groupsum/npmctl/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
  <a href="https://github.com/groupsum/npmctl/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License"></a>
</p>

<p align="center">
  <a href="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-godaddy/README.md/"><img src="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-godaddy/README.md.svg?label=npmctl-godaddy%20package%20hits" alt="npmctl-godaddy package hits"></a>
  <a href="https://pepy.tech/projects/npmctl-godaddy"><img src="https://static.pepy.tech/badge/npmctl-godaddy" alt="npmctl-godaddy downloads"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/groupsum/npmctl/master/docs/images/marketing/npmctl-architecture-infographic.png" alt="npmctl architecture infographic">
</p>

`npmctl-godaddy` is the GoDaddy DNS provider package for `npmctl`. Install it when you want desired-state DNS records or DNS diagnostics to resolve through GoDaddy instead of using only the base `npmctl` package.

## Supported Python Versions

`npmctl-godaddy` supports Python `3.10`, `3.11`, `3.12`, `3.13`, and `3.14`.

## Why npmctl-godaddy

- Adds GoDaddy DNS provider discovery to `npmctl`
- Lets DNS workflows live beside proxy and certificate desired state
- Keeps GoDaddy API keys out of the core CLI package
- Supports operator diagnostics through `npmctl dns doctor`
- Documents GoDaddy's record-set replacement behavior for safer automation

## FAQ

### What is npmctl-godaddy?

**Answer:** `npmctl-godaddy` is a plugin package that teaches `npmctl` how to talk to the GoDaddy Domains API for DNS record operations and DNS provider diagnostics.

### When do I need npmctl-godaddy?

**Answer:** You need `npmctl-godaddy` when your `npmctl` workflow includes GoDaddy-managed DNS records or when you want `npmctl` to validate GoDaddy DNS connectivity and credentials.

### Does npmctl-godaddy work without npmctl?

**Answer:** No. `npmctl-godaddy` is an extension package for `npmctl`, not a standalone CLI.

### Can npmctl-godaddy set A and CNAME records?

**Answer:** Yes. GoDaddy's Domains API supports A and CNAME records. Its DNS mutation endpoint replaces all records for one `{type, name}` pair, so preserve existing values when managing multi-value records.

### What credentials are required?

**Answer:** GoDaddy API access requires `GODADDY_API_KEY` and `GODADDY_API_SECRET`. Account protection, domain locks, or product eligibility can still block DNS mutations even when credentials are valid.

## Install

Install the base CLI and the GoDaddy provider package together:

```bash
pipx install npmctl
pipx inject npmctl npmctl-godaddy
npmctl plugins list
```

With `uv`:

```bash
uv tool install npmctl
uv tool install npmctl-godaddy
npmctl plugins list
```

Inside a virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install npmctl npmctl-godaddy
npmctl plugins list
```

## Configure GoDaddy

Set the required environment variables:

```bash
export GODADDY_API_KEY=your-api-key
export GODADDY_API_SECRET=your-api-secret
```

Optional for tests or alternate endpoints:

```bash
export GODADDY_API_BASE_URL=https://api.godaddy.com
```

## Verify Plugin Discovery

Check that `npmctl` can discover the provider:

```bash
npmctl plugins list
npmctl dns doctor --provider godaddy
```

## Minimal DNS Workflow

Once the provider is installed and configured, `npmctl` can validate or diagnose GoDaddy-backed DNS behavior through the base CLI:

```bash
npmctl dns providers
npmctl dns zones --provider godaddy
npmctl dns records --provider godaddy --zone example.com
```

## GoDaddy API Surface

The provider follows the GoDaddy Domains API DNS record surface:

- `GET /v1/domains`: discover domains in the account.
- `GET /v1/domains/{domain}/records`: list all DNS records for one domain.
- `GET /v1/domains/{domain}/records/{type}/{name}`: list records for one type and name.
- `PUT /v1/domains/{domain}/records/{type}/{name}`: replace the full record set for one type and name.
- `DELETE /v1/domains/{domain}/records/{type}/{name}`: delete records for one type and name.

## Programmatic Record Operations

`create_record()` is a convenience wrapper that replaces a `{type, name}` pair with one record. Use `replace_records()` when preserving multiple values for the same record name and type:

```python
from npmctl_godaddy import GoDaddyClient, GoDaddyConfig

client = GoDaddyClient(GoDaddyConfig.from_env())
client.create_record("example.com", type="A", name="www", value="192.0.2.10", ttl=600)
client.replace_records(
    "example.com",
    type="CNAME",
    name="app",
    records=[{"data": "target.example.net", "ttl": 600}],
)
client.delete_records("example.com", type="A", name="www")
```

## Safety Notes

- GoDaddy `PUT` replaces all records for the selected `{type, name}` pair.
- Account-level domain locks, premium DNS status, protection settings, or product eligibility may block API changes even when credentials are valid.
- Use least-privilege keys where available and avoid broad automation over unrelated domains.
- Use npmctl owner metadata for desired DNS records so future apply support can remain owner-scoped.

## More Documentation

- Related PyPI package: https://pypi.org/project/npmctl/
- Repository: https://github.com/groupsum/npmctl
- DNS provider docs: https://github.com/groupsum/npmctl/tree/master/docs/dns-providers.md
