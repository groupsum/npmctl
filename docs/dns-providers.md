# DNS provider packages

npmctl DNS providers are Python extension packages registered through the
`npmctl.dns_providers` entry point group. The base provider contract requires
`name`, `zones()`, and `records(zone)`. Providers that participate in
`npmctl apply` must also expose `apply_records(zone, records)` so the core DNS
reconciler can fail closed when a provider is read-only.

## Supported provider packages

| Package | Provider name | API family | Supported writes | Mutation model |
| --- | --- | --- | --- | --- |
| `npmctl-namecheap` | `namecheap` | Namecheap XML API | A, AAAA, CNAME, TXT, MX, SRV, CAA | registrar host records |
| `npmctl-cloudflare` | `cloudflare` | Cloudflare DNS Records API | A, AAAA, CNAME, TXT, MX, SRV, CAA | create, put, patch, delete records |
| `npmctl-route53` | `route53` | AWS Route 53 API | A, AAAA, CNAME, TXT, MX, SRV, CAA | `ChangeResourceRecordSets` batches |
| `npmctl-digitalocean` | `digitalocean` | DigitalOcean Domain Records API | A, AAAA, CNAME, TXT, MX, SRV, CAA | create, update, delete records |
| `npmctl-godaddy` | `godaddy` | GoDaddy Domains API | A, AAAA, CNAME, TXT, MX, SRV, CAA | replace records by `{type, name}` |

All provider writers accept the npmctl DNS record schema types `A`, `AAAA`,
`CNAME`, `TXT`, `MX`, `SRV`, and `CAA`. MX records require `priority`; other
record types reject `priority` at schema validation time.

## Cloudflare

`npmctl-cloudflare` uses Cloudflare's DNS Records API:

- `GET /zones`
- `GET /zones/{zone_id}/dns_records`
- `POST /zones/{zone_id}/dns_records`
- `PUT /zones/{zone_id}/dns_records/{dns_record_id}`
- `PATCH /zones/{zone_id}/dns_records/{dns_record_id}`
- `DELETE /zones/{zone_id}/dns_records/{dns_record_id}`

Use `CLOUDFLARE_API_TOKEN` with zone read and DNS read/write permissions scoped
to the target zone.

## AWS Route 53

`npmctl-route53` uses Route 53 through `boto3`:

- `ListHostedZones`
- `ListResourceRecordSets`
- `ChangeResourceRecordSets` with `CREATE`, `UPSERT`, and `DELETE`

Use the standard AWS credential chain or `ROUTE53_PROFILE`. IAM should be scoped
to the target hosted zone where possible.

## DigitalOcean

`npmctl-digitalocean` uses DigitalOcean's Domains API:

- `GET /v2/domains`
- `GET /v2/domains/{domain_name}/records`
- `POST /v2/domains/{domain_name}/records`
- `PUT /v2/domains/{domain_name}/records/{domain_record_id}`
- `DELETE /v2/domains/{domain_name}/records/{domain_record_id}`

Use `DIGITALOCEAN_TOKEN` with domain record permissions.

## GoDaddy

`npmctl-godaddy` uses GoDaddy's Domains API:

- `GET /v1/domains`
- `GET /v1/domains/{domain}/records`
- `GET /v1/domains/{domain}/records/{type}/{name}`
- `PUT /v1/domains/{domain}/records/{type}/{name}`
- `DELETE /v1/domains/{domain}/records/{type}/{name}`

GoDaddy's `PUT` route replaces the full record set for one `{type, name}` pair.
Use `replace_records()` when multiple values exist for the same record name and
type.

## Operator guardrails

- The authoritative DNS host for a zone must match the configured provider.
- Credentials should be scoped to the target account, hosted zone, or domain.
- Desired DNS records must keep npmctl owner metadata so apply and prune behavior
  remain explicit, owner-scoped, and safe against foreign-owned resources.
- Provider apply rewrites only the selected provider zone payload; unmanaged
  records returned by the provider are preserved unless they carry matching
  npmctl ownership metadata and are omitted from desired state during
  owner-scoped pruning.
