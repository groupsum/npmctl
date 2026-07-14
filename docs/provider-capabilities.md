# Provider capabilities

Every bundled DNS provider declares a versioned mutation model, supported record types, readback behavior, lease requirements, idempotency, rollback, and forward-repair support. npmctl checks the declaration before mutation and requires a verified post-mutation digest from modern providers. Legacy providers remain usable through a conservative read-only capability adapter during the 0.x transition.
