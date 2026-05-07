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
