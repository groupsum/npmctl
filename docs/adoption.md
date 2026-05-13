# Adoption

`npmctl adopt` is used to bring manual NPM resources under declarative management. Default adoption is strict: the unmanaged resource must match desired fields before metadata is written.

Use `--allow-field-drift` or `--force` only when intentionally claiming and overwriting unmanaged state.

Repair-safe adoption controls:

- `--metadata-only` only writes managed metadata to compatible unmanaged resources and never creates adjacent resources.
- `--only proxy_hosts|certificates|access_lists|...` scopes adoption to specific resource families.
- default `adopt` certificate policy is `--certificate-mode=reuse`, so adoption prefers compatible live certificates instead of new issuance.
