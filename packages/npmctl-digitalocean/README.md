<h1 align="center">npmctl-digitalocean</h1>

<p align="center"><strong>DigitalOcean DNS provider plugin for npmctl</strong></p>

<p align="center">
  Extend <code>npmctl</code> with DigitalOcean-backed DNS record management for declarative workflows, provider discovery, and DNS-aware automation.
</p>

<p align="center">
  <a href="https://pypi.org/project/npmctl-digitalocean/"><img src="https://img.shields.io/pypi/v/npmctl-digitalocean.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/npmctl-digitalocean/"><img src="https://img.shields.io/pypi/pyversions/npmctl-digitalocean.svg" alt="Python versions"></a>
  <a href="https://github.com/groupsum/npmctl/actions/workflows/ci.yml"><img src="https://github.com/groupsum/npmctl/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
  <a href="https://github.com/groupsum/npmctl/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License"></a>
</p>

<p align="center">
  <a href="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-digitalocean/README.md/"><img src="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-digitalocean/README.md.svg?label=npmctl-digitalocean%20package%20hits" alt="npmctl-digitalocean package hits"></a>
  <a href="https://pepy.tech/projects/npmctl-digitalocean"><img src="https://static.pepy.tech/badge/npmctl-digitalocean" alt="npmctl-digitalocean downloads"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/groupsum/npmctl/master/docs/images/marketing/npmctl-architecture-infographic.png" alt="npmctl architecture infographic">
</p>

`npmctl-digitalocean` is the DigitalOcean DNS provider package for `npmctl`. Install it when you want desired-state DNS records or DNS diagnostics to resolve through DigitalOcean instead of using only the base `npmctl` package.

## Supported Python Versions

`npmctl-digitalocean` supports Python `3.10`, `3.11`, `3.12`, `3.13`, and `3.14`.

## Why npmctl-digitalocean

- Adds DigitalOcean DNS provider discovery to `npmctl`
- Lets DNS workflows live beside proxy and certificate desired state
- Keeps DigitalOcean tokens out of the core CLI package
- Supports operator diagnostics through `npmctl dns doctor`
- Provides client helpers for DigitalOcean A and CNAME record workflows

## FAQ

### What is npmctl-digitalocean?

**Answer:** `npmctl-digitalocean` is a plugin package that teaches `npmctl` how to talk to the DigitalOcean Domain Records API for DNS record operations and DNS provider diagnostics.

### When do I need npmctl-digitalocean?

**Answer:** You need `npmctl-digitalocean` when your `npmctl` workflow includes DigitalOcean-managed DNS records or when you want `npmctl` to validate DigitalOcean DNS connectivity and credentials.

### Does npmctl-digitalocean work without npmctl?

**Answer:** No. `npmctl-digitalocean` is an extension package for `npmctl`, not a standalone CLI.

### Can npmctl-digitalocean set A and CNAME records?

**Answer:** Yes. DigitalOcean's Domain Records API supports A and CNAME records, and this package exposes helpers for create, update, and delete operations.

### What credentials are required?

**Answer:** DigitalOcean API access requires `DIGITALOCEAN_TOKEN`. For diagnostics, the token needs domain read permissions. For record changes, it needs write access to target domain records.

## Install

Install the base CLI and the DigitalOcean provider package together:

```bash
pipx install npmctl
pipx inject npmctl npmctl-digitalocean
npmctl plugins list
```

With `uv`:

```bash
uv tool install npmctl
uv tool install npmctl-digitalocean
npmctl plugins list
```

Inside a virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install npmctl npmctl-digitalocean
npmctl plugins list
```

## Configure DigitalOcean

Set the required environment variable:

```bash
export DIGITALOCEAN_TOKEN=your-digitalocean-token
```

Optional for tests or alternate endpoints:

```bash
export DIGITALOCEAN_API_BASE_URL=https://api.digitalocean.com
```

## Verify Plugin Discovery

Check that `npmctl` can discover the provider:

```bash
npmctl plugins list
npmctl dns doctor --provider digitalocean
```

## Minimal DNS Workflow

Once the provider is installed and configured, `npmctl` can validate or diagnose DigitalOcean-backed DNS behavior through the base CLI:

```bash
npmctl dns providers
npmctl dns zones --provider digitalocean
npmctl dns records --provider digitalocean --zone example.com
```

## DigitalOcean API Surface

The provider follows the DigitalOcean Domains and Domain Records API:

- `GET /v2/domains`: discover domains managed in the account.
- `GET /v2/domains/{domain_name}/records`: list DNS records for one domain.
- `POST /v2/domains/{domain_name}/records`: create A, CNAME, and other supported records.
- `PUT /v2/domains/{domain_name}/records/{domain_record_id}`: update a record.
- `DELETE /v2/domains/{domain_name}/records/{domain_record_id}`: delete a record.

## Programmatic Record Operations

```python
from npmctl_digitalocean import DigitalOceanClient, DigitalOceanConfig

client = DigitalOceanClient(DigitalOceanConfig.from_env())
record = client.create_record("example.com", type="A", name="www", value="192.0.2.10", ttl=300)
client.update_record("example.com", int(record.record_id), type="A", name="www", value="192.0.2.11", ttl=300)
client.delete_record("example.com", int(record.record_id))
```

CNAME records use `type="CNAME"` and place the target host in `value`.

## Safety Notes

- DigitalOcean record `name` is relative to the zone; use `@` for the root where applicable.
- Keep `DIGITALOCEAN_TOKEN` out of desired-state files and logs.
- Use account and token scoping to avoid mutating foreign-owned DNS.
- Use npmctl owner metadata for desired DNS records so future apply support can remain owner-scoped.

## More Documentation

- Related PyPI package: https://pypi.org/project/npmctl/
- Repository: https://github.com/groupsum/npmctl
- DNS provider docs: https://github.com/groupsum/npmctl/tree/master/docs/dns-providers.md
