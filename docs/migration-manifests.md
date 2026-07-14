# Migration manifests

A schema-1 `NpmctlMigration` records source and target versions and digests, exact operations, approvals, destructive/adoption policy, and recovery classification. Planning is side-effect free. Execution checks every source digest, stages every output, writes backups, replaces files transactionally, and appends start/completion records to a chained ledger.
