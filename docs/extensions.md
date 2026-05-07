# Extensions

npmctl exposes typed plugin contracts in `npmctl.plugins`.

`ResourceProvider` defines the contract for custom managed resource kinds:

- `identity(payload)` returns owner and resource id.
- `natural_key(payload)` returns the resource natural key.
- `desired_payload(payload)` returns the API payload.

`CertificateProvider` defines the contract for external certificate resolution:

- `resolve(reference)` returns an NPM-compatible certificate payload.

`DnsProvider` defines the contract for DNS provider inspection:

- `zones()` returns available zones.
- `records(zone)` returns records for one zone.

`PluginRegistry` is a small in-memory registration surface for embedding and
tests. It also supports runtime discovery through Python package entry points:

- `npmctl.resource_providers`
- `npmctl.certificate_providers`
- `npmctl.dns_providers`

Discovered providers are validated before registration. Invalid providers fail
predictably instead of being silently ignored, and `npmctl plugins list` reports
the active resource and certificate provider names for operator diagnostics.

Desired-state loading invokes registered providers for `plugin_resources` and
`external_certificates`. Resource providers must expose a supported generic
resource `kind`, `identity(payload)`, `natural_key(payload)`, and
`desired_payload(payload)`. Certificate providers must expose `resolve(reference)`;
the resolved payload is parsed through the normal certificate model so owner
scope, metadata validation, planning, and apply behavior remain unchanged.

DNS providers must expose `name`, `zones()`, and `records(zone)`. The
provider-neutral desired-state model for DNS records is available in schema v2
as `dns_records`.
