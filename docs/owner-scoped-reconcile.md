# Owner-scoped reconciliation

Owner scope is the primary safety boundary. A resource owned by `workload-a` cannot be mutated by `workload-b`.

Plan outcomes:

- `create`: missing desired resource.
- `update`: owned resource differs from desired state.
- `delete`: owned resource absent from desired state and `--prune-owned` is set.
- `adopt`: unmanaged resource is explicitly claimed by metadata.
- `noop`: resource already converged.
- `conflict`: unsafe or unsupported operation.
