<h1 align="center">npmctl-cloudflare</h1>

<p align="center"><strong>Cloudflare DNS provider plugin for npmctl</strong></p>

`npmctl-cloudflare` registers a `cloudflare` DNS provider for `npmctl`. It is designed for Cloudflare-hosted zones where operators need provider discovery, DNS diagnostics, and API-backed A and CNAME record workflows beside Nginx Proxy Manager desired state.

## Supported Python Versions

`npmctl-cloudflare` supports Python `3.10`, `3.11`, `3.12`, `3.13`, and `3.14`.

## Package Metadata

- Trove lifecycle classifier: `Development Status :: 1 - Planning`
- Entry point group: `npmctl.dns_providers`
- Entry point name: `cloudflare`
- Runtime dependency: `requests`
- Credential source: environment variables

## Cloudflare API Surface

The provider follows the current Cloudflare DNS Records API:

- `GET /zones`: discover zones available to the token.
- `GET /zones/{zone_id}/dns_records`: list DNS records in one zone.
- `POST /zones/{zone_id}/dns_records`: create A, CNAME, and other supported records.
- `PUT /zones/{zone_id}/dns_records/{dns_record_id}`: overwrite an existing record.
- `PATCH /zones/{zone_id}/dns_records/{dns_record_id}`: partially update an existing record.
- `DELETE /zones/{zone_id}/dns_records/{dns_record_id}`: delete a record.

Cloudflare accepts scoped API tokens. For read-only diagnostics, grant `Zone:Read` and `DNS:Read`. For create, update, or delete operations, grant `DNS:Write` for the target zone.

Cloudflare DNS constraints are enforced by the API. Notably, A and AAAA records cannot coexist with a CNAME on the same name, and NS records cannot coexist with other record types on the same name.

## Configure

```bash
export CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
```

Optional for tests, proxies, or non-default API endpoints:

```bash
export CLOUDFLARE_API_BASE_URL=https://api.cloudflare.com/client/v4
```

## Install

```bash
pipx install npmctl
pipx inject npmctl npmctl-cloudflare
npmctl plugins list
```

With `uv`:

```bash
uv tool install npmctl
uv tool install npmctl-cloudflare
npmctl dns doctor --provider cloudflare
```

## Verify Discovery

```bash
npmctl plugins list
npmctl dns providers
npmctl dns doctor --provider cloudflare
npmctl dns zones --provider cloudflare
npmctl dns records --provider cloudflare --zone example.com
```

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
- Use npmctl owner metadata for desired DNS records so future apply support can remain owner-scoped.
