# Namecheap DNS Apply Gap

Date: 2026-05-18

## Summary

`npmctl` schema v2 accepts `dns_records`, and `npmctl-namecheap` registers a
`namecheap` DNS provider. The current PyPI packages do not mutate Namecheap DNS
records. They can validate desired-state YAML and inspect provider records, but
`npmctl apply desired-state/dns.yaml` does not create, update, or remove
Namecheap records.

This creates a false-positive deployment path for site repositories whose DNS
workflows run:

```bash
npmctl validate .tmp/dns.yaml
npmctl dns doctor --provider namecheap
npmctl plan .tmp/dns.yaml --owner <site>
npmctl apply .tmp/dns.yaml --owner <site>
```

Those commands can complete without changing Namecheap host records.

## Observed Versions

The gap was reproduced with packages installed from PyPI into a local virtual
environment:

```text
npmctl==0.3.7
npmctl-namecheap==0.3.7
```

## Evidence

The installed `npmctl-namecheap` provider exposes only read operations:

```python
class NamecheapDnsProvider:
    name = "namecheap"

    def zones(self) -> tuple[str, ...]:
        return self.client.zones()

    def records(self, zone: str) -> tuple[dict[str, object], ...]:
        return tuple(record.to_dict() for record in self.client.records(zone))
```

The installed Namecheap client only calls:

```text
namecheap.domains.getList
namecheap.domains.dns.getHosts
```

It does not call:

```text
namecheap.domains.dns.setHosts
```

`setHosts` is required by the Namecheap XML API to persist changed host records.

The installed `npmctl` loader parses `dns_records`, and `npmctl validate` counts
them, but the generic owner-scoped NPM plan/apply engine is focused on Nginx
Proxy Manager resources. `dns_records` are not routed into a DNS reconciliation
engine that calls provider write methods.

## Operational Impact

Site repositories can report successful DNS workflows while Namecheap remains
unchanged. Operators then observe:

- stale DNS records still present in Namecheap
- old records not removed
- new apex or `www` records not created
- public DNS still resolving old state or failing to resolve
- misleading CI/CD status, because the DNS job says success without a mutation

This affected lander repositories declaring DNS in `desired-state/dns.yaml`,
including records such as:

```yaml
dns_records:
  - provider: namecheap
    zone: example.com
    type: A
    name: "@"
    value: __SITE_SERVER_IP__
    ttl: 300
```

## Expected Behavior

`npmctl plan desired-state/dns.yaml --owner <site>` should include DNS operations
for the selected owner:

```text
create dns_record example.com @ A
update dns_record example.com www CNAME
delete dns_record example.com stale-owned-record
noop dns_record example.com already converged
```

`npmctl apply desired-state/dns.yaml --owner <site>` should persist those
changes through the selected provider.

For Namecheap, apply must use `namecheap.domains.dns.setHosts` with the complete
zone host set required by the Namecheap API.

## Required Implementation

Add a DNS reconciliation layer to `npmctl`:

- include `dns_records` in plan/apply instead of only validate/load paths
- group desired records by provider and zone
- fetch current provider records
- compute create, update, delete, and noop operations
- restrict destructive deletes to records owned by the requested owner or
  explicitly marked as managed by npmctl
- fail closed when provider write support is unavailable
- report DNS mutations separately from Nginx Proxy Manager mutations

Extend the DNS provider protocol:

```python
class DnsProvider(Protocol):
    def zones(self) -> tuple[str, ...]: ...
    def records(self, zone: str) -> tuple[dict[str, Any], ...]: ...
    def apply_records(self, zone: str, records: tuple[dict[str, Any], ...]) -> None: ...
```

Add Namecheap write support:

- implement `NamecheapClient.set_hosts(zone, records)`
- call `namecheap.domains.dns.setHosts`
- preserve unmanaged Namecheap records in the zone payload
- translate npmctl DNS records into Namecheap `HostName`, `RecordType`,
  `Address`, `TTL`, and `MXPref` fields
- support at least A and CNAME for the current site use case
- validate `NAMECHEAP_CLIENT_IP` before apply

## Acceptance Criteria

- `npmctl validate` still validates `dns_records`.
- `npmctl plan desired-state/dns.yaml --owner <site>` shows DNS operations.
- `npmctl apply desired-state/dns.yaml --owner <site>` calls provider write
  methods and fails if the provider is read-only.
- `npmctl-namecheap` can create or update apex A records and `www` CNAME
  records.
- Old npmctl-owned Namecheap records are removed when omitted from desired
  state.
- Unmanaged records in the same zone are preserved.
- A post-apply `npmctl dns records --provider namecheap --zone <zone>` reflects
  the desired records.
- Site DNS workflows fail when `NAMECHEAP_CLIENT_IP` or `SITE_SERVER_IP` is
  missing.

## Suggested Tests

Add unit tests for the Namecheap provider:

- renders `setHosts` parameters for A and CNAME records
- preserves unmanaged records returned by `getHosts`
- removes stale npmctl-owned records from the next `setHosts` payload
- raises a clear error when `NAMECHEAP_CLIENT_IP` is missing
- handles Namecheap API XML errors without leaking secrets

Add npmctl planner/apply tests:

- `dns_records` produce DNS plan operations
- owner scoping limits DNS deletions
- read-only DNS providers fail apply with an actionable message
- mixed Nginx Proxy Manager and DNS desired-state files plan both surfaces

## Interim Operator Guidance

Until this gap is fixed and released, do not treat successful `npmctl` DNS
workflow runs as proof that Namecheap was changed. Verify through either:

```bash
npmctl dns records --provider namecheap --zone <zone>
```

with `NAMECHEAP_CLIENT_IP` configured, or through the Namecheap UI/API directly.
