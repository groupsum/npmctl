# Schema migrations

Desired-state schema migrations are deterministic and explicit.

```bash
npmctl migrate infra/npm/desired-state --check
npmctl migrate infra/npm/desired-state --write
```

Version 1 is the first public schema. Legacy documents without headers migrate by adding `apiVersion`, `schemaVersion`, and empty missing resource lists.
