# Security and integrity

npmctl never logs tokens intentionally. GitHub workflows use concurrency to avoid concurrent mutation. Metadata ownership prevents foreign workload mutation. Prune/delete is opt-in and owner-scoped.
