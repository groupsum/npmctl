<h1 align="center">npmctl-cloudflare</h1>

<p align="center"><strong>Cloudflare DNS provider plugin for npmctl</strong></p>

<p align="center">
  Extend <code>npmctl</code> with Cloudflare-backed DNS record management for declarative workflows, provider discovery, and DNS-aware automation.
</p>

<p align="center">
  <a href="https://pypi.org/project/npmctl-cloudflare/"><img src="https://img.shields.io/pypi/v/npmctl-cloudflare.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/npmctl-cloudflare/"><img src="https://img.shields.io/pypi/pyversions/npmctl-cloudflare.svg" alt="Python versions"></a>
  <a href="https://github.com/groupsum/npmctl/actions/workflows/ci.yml"><img src="https://github.com/groupsum/npmctl/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
  <a href="https://github.com/groupsum/npmctl/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License"></a>
</p>

<p align="center">
  <a href="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-cloudflare/README.md/"><img src="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-cloudflare/README.md.svg?label=npmctl-cloudflare%20package%20hits" alt="npmctl-cloudflare package hits"></a>
  <a href="https://pepy.tech/projects/npmctl-cloudflare"><img src="https://static.pepy.tech/badge/npmctl-cloudflare" alt="npmctl-cloudflare downloads"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/groupsum/npmctl/master/docs/images/marketing/npmctl-architecture-infographic.png" alt="npmctl architecture infographic">
</p>

`npmctl-cloudflare` is the Cloudflare DNS provider package for `npmctl`. Install it when you want desired-state DNS records or DNS diagnostics to resolve through Cloudflare instead of using only the base `npmctl` package.

## Supported Python Versions

`npmctl-cloudflare` supports Python `3.10`, `3.11`, `3.12`, `3.13`, and `3.14`.

## Why npmctl-cloudflare

- Adds Cloudflare DNS provider discovery to `npmctl`
- Lets DNS workflows live beside proxy and certificate desired state
- Keeps Cloudflare API tokens out of the core CLI package
- Supports operator diagnostics through `npmctl dns doctor`
- Provides client helpers for Cloudflare A and CNAME record workflows

## FAQ

### What is npmctl-cloudflare?

**Answer:** `npmctl-cloudflare` is a plugin package that teaches `npmctl` how to talk to the Cloudflare DNS Records API for DNS record operations and DNS provider diagnostics.

### When do I need npmctl-cloudflare?

**Answer:** You need `npmctl-cloudflare` when your `npmctl` workflow includes Cloudflare-managed DNS records or when you want `npmctl` to validate Cloudflare DNS connectivity and credentials.

### Does npmctl-cloudflare work without npmctl?

**Answer:** No. `npmctl-cloudflare` is an extension package for `npmctl`, not a standalone CLI.

### Can npmctl-cloudflare set A and CNAME records?

**Answer:** Yes. The Cloudflare DNS Records API supports A and CNAME records, and this package exposes helpers for create, replace, patch, and delete operations.

### What credentials are required?

**Answer:** Cloudflare API access requires `CLOUDFLARE_API_TOKEN`. For diagnostics, grant zone read and DNS read access. For record changes, grant DNS write access to the target zone.

## Install

Install the base CLI and the Cloudflare provider package together:

```bash
pipx install npmctl
pipx inject npmctl npmctl-cloudflare
npmctl plugins list
```

With `uv`:

```bash
uv tool install npmctl
uv tool install npmctl-cloudflare
npmctl plugins list
```

Inside a virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install npmctl npmctl-cloudflare
npmctl plugins list
```

## Configure Cloudflare

Set the required environment variable:

```bash
export CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
```

Optional for tests, proxies, or alternate endpoints:

```bash
export CLOUDFLARE_API_BASE_URL=https://api.cloudflare.com/client/v4
```

## Verify Plugin Discovery

Check that `npmctl` can discover the provider:

```bash
npmctl plugins list
npmctl dns doctor --provider cloudflare
```

## Minimal DNS Workflow

Once the provider is installed and configured, `npmctl` can validate or diagnose Cloudflare-backed DNS behavior through the base CLI:

```bash
npmctl dns providers
npmctl dns zones --provider cloudflare
npmctl dns records --provider cloudflare --zone example.com
```

## Cloudflare API Surface

The provider follows the Cloudflare DNS Records API:

- `GET /zones`: discover zones available to the token.
- `GET /zones/{zone_id}/dns_records`: list DNS records in one zone.
- `POST /zones/{zone_id}/dns_records`: create A, CNAME, and other supported records.
- `PUT /zones/{zone_id}/dns_records/{dns_record_id}`: overwrite an existing record.
- `PATCH /zones/{zone_id}/dns_records/{dns_record_id}`: partially update an existing record.
- `DELETE /zones/{zone_id}/dns_records/{dns_record_id}`: delete a record.

## Programmatic Record Operations

The npmctl DNS provider contract requires `zones()` and `records(zone)`. This package also exposes client helpers for API-backed record mutation:

```python
from npmctl_cloudflare import CloudflareClient, CloudflareConfig

client = CloudflareClient(CloudflareConfig.from_env())
record = client.create_record("example.com", type="A", name="www", value="192.0.2.10", ttl=300)
client.patch_record("example.com", str(record.record_id), value="192.0.2.11")
client.delete_record("example.com", str(record.record_id))
```

CNAME creation uses the same method:

```python
client.create_record("example.com", type="CNAME", name="app", value="target.example.net", ttl=300)
```

## Safety Notes

- Only operate on zones that are authoritative in Cloudflare.
- Use least-privilege API tokens scoped to the intended zone.
- Keep `CLOUDFLARE_API_TOKEN` out of desired-state files and logs.
- Cloudflare prevents CNAME records from coexisting with A or AAAA records on the same name.
- Use npmctl owner metadata for desired DNS records so future apply support can remain owner-scoped.

## More Documentation

- Related PyPI package: https://pypi.org/project/npmctl/
- Repository: https://github.com/groupsum/npmctl
- DNS provider docs: https://github.com/groupsum/npmctl/tree/master/docs/dns-providers.md
