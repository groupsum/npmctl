# Namecheap DNS extension

`npmctl-namecheap` registers a `namecheap` DNS provider with npmctl through the
`npmctl.dns_providers` entry point group.

Configuration is read from environment variables:

- `NAMECHEAP_API_USER`
- `NAMECHEAP_API_KEY`
- `NAMECHEAP_USERNAME`
- `NAMECHEAP_CLIENT_IP`
- `NAMECHEAP_API_BASE_URL` for test or non-default API endpoints

The provider uses Namecheap's XML API to list zones and records for diagnostics
and to persist desired DNS state during `npmctl apply`.
Desired-state DNS records are modeled in npmctl schema v2 under `dns_records`.

Namecheap applies host records through `namecheap.domains.dns.setHosts`, which
requires a complete zone host payload. npmctl builds that payload from the
current Namecheap records plus the desired npmctl-owned records, preserving
unmanaged records in the same zone and removing stale npmctl-owned records when
owner-scoped pruning is requested.

The Namecheap writer supports A, AAAA, CNAME, TXT, MX, SRV, and CAA records for
declarative apply. MX records require `priority`; other record types reject
`priority` at schema validation time. The writer validates
`NAMECHEAP_CLIENT_IP` before mutation and redacts configured Namecheap
credential values from API error messages.
