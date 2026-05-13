<h1 align="center">npmctl-namecheap</h1>

<p align="center"><strong>Namecheap DNS provider plugin for npmctl</strong></p>

<p align="center">
  Extend <code>npmctl</code> with Namecheap-backed DNS record management for declarative workflows, provider discovery, and DNS-aware automation.
</p>

<p align="center">
  <a href="https://pypi.org/project/npmctl-namecheap/"><img src="https://img.shields.io/pypi/v/npmctl-namecheap.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/npmctl-namecheap/"><img src="https://img.shields.io/pypi/pyversions/npmctl-namecheap.svg" alt="Python versions"></a>
  <a href="https://github.com/groupsum/npmctl/actions/workflows/ci.yml"><img src="https://github.com/groupsum/npmctl/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
  <a href="https://github.com/groupsum/npmctl/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache 2.0 License"></a>
</p>

<p align="center">
  <a href="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-namecheap/README.md/"><img src="https://hits.sh/github.com/groupsum/npmctl/blob/master/packages/npmctl-namecheap/README.md.svg?label=npmctl-namecheap%20package%20hits" alt="npmctl-namecheap package hits"></a>
  <a href="https://pepy.tech/projects/npmctl-namecheap"><img src="https://static.pepy.tech/badge/npmctl-namecheap" alt="npmctl-namecheap downloads"></a>
</p>

`npmctl-namecheap` is the Namecheap DNS provider package for `npmctl`. Install it when you want desired-state DNS records or DNS diagnostics to resolve through Namecheap instead of using only the base `npmctl` package.

## Supported Python Versions

`npmctl-namecheap` supports Python `3.10`, `3.11`, `3.12`, `3.13`, and `3.14`.

## Why npmctl-namecheap

- Adds Namecheap DNS provider discovery to `npmctl`
- Lets DNS workflows live beside proxy and certificate desired state
- Keeps provider-specific credentials out of the core CLI package
- Supports operator diagnostics through `npmctl dns doctor`

## FAQ

### What is npmctl-namecheap?

**Answer:** `npmctl-namecheap` is a plugin package that teaches `npmctl` how to talk to the Namecheap DNS API for DNS record operations and DNS provider diagnostics.

### When do I need npmctl-namecheap?

**Answer:** You need `npmctl-namecheap` when your `npmctl` workflow includes Namecheap-managed DNS records or when you want `npmctl` to validate Namecheap DNS connectivity and credentials.

### Does npmctl-namecheap work without npmctl?

**Answer:** No. `npmctl-namecheap` is an extension package for `npmctl`, not a standalone CLI.

### What credentials are required?

**Answer:** Namecheap API access requires `NAMECHEAP_API_USER`, `NAMECHEAP_API_KEY`, `NAMECHEAP_USERNAME`, and `NAMECHEAP_CLIENT_IP`. You can also override the endpoint with `NAMECHEAP_API_BASE_URL` for tests or non-default environments.

## Install

Install the base CLI and the Namecheap provider package together:

```bash
pipx install npmctl
pipx inject npmctl npmctl-namecheap
npmctl plugins list
```

With `uv`:

```bash
uv tool install npmctl
uv tool install npmctl-namecheap
npmctl plugins list
```

Inside a virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install npmctl npmctl-namecheap
npmctl plugins list
```

## Configure Namecheap

Set the required environment variables:

```bash
export NAMECHEAP_API_USER=your-api-user
export NAMECHEAP_API_KEY=your-api-key
export NAMECHEAP_USERNAME=your-username
export NAMECHEAP_CLIENT_IP=your-public-ip
```

Optional for tests or alternate endpoints:

```bash
export NAMECHEAP_API_BASE_URL=https://api.namecheap.com/xml.response
```

## Verify Plugin Discovery

Check that `npmctl` can discover the provider:

```bash
npmctl plugins list
npmctl dns doctor --provider namecheap
```

## Minimal DNS Workflow

Once the provider is installed and configured, `npmctl` can validate or diagnose Namecheap-backed DNS behavior through the base CLI:

```bash
npmctl dns doctor --provider namecheap
```

## More Documentation

- Related PyPI package: https://pypi.org/project/npmctl/
- Repository: https://github.com/groupsum/npmctl
- Provider docs: https://github.com/groupsum/npmctl/tree/master/docs/namecheap.md
