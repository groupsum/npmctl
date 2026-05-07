# Namecheap DNS extension

`npmctl-namecheap` registers a `namecheap` DNS provider with npmctl through the
`npmctl.dns_providers` entry point group.

Configuration is read from environment variables:

- `NAMECHEAP_API_USER`
- `NAMECHEAP_API_KEY`
- `NAMECHEAP_USERNAME`
- `NAMECHEAP_CLIENT_IP`
- `NAMECHEAP_API_BASE_URL` for test or non-default API endpoints

The provider uses Namecheap's XML API to list zones and records for diagnostics.
Desired-state DNS records are modeled in npmctl schema v2 under `dns_records`.
