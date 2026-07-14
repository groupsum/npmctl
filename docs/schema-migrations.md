# Schema migrations

Desired-state schema migrations are deterministic and explicit.

```bash
npmctl migrate infra/npm/desired-state --check
npmctl migrate infra/npm/desired-state --write
```

Version 1 is the first public schema. Legacy documents without headers migrate by adding `apiVersion`, `schemaVersion`, and empty missing resource lists.

Version 2 adds provider-backed DNS records under `dns_records`. Migration from
v1 to v2 preserves existing resources and adds `dns_records: []` when the
document does not already declare DNS records.

Version 3 introduces the `DesiredState` kind with `metadata` and `spec` envelopes and camel-case collection names. Migrations are adjacent (`v1 -> v2 -> v3`), reversible where an inverse is defined, and executed from reviewed manifests rather than as an implicit side effect of load or apply.
