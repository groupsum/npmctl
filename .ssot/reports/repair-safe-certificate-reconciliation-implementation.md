# Repair-safe certificate reconciliation implementation

Date: 2026-05-12

Implemented boundary: `bnd:npmctl-repair-safe-certificate-reconciliation`

Delivered behavior:

- adopt supports `--metadata-only` and `--only ...` resource-family scoping
- planner distinguishes compatible unmanaged resources that are adoptable from unmanaged conflicts that remain unsafe
- certificate reconcile supports `--certificate-mode=reuse|create|rotate`
- compatible live certificates are reused by normalized provider and domain set when policy allows reuse
- certificate issuance attempts are deduplicated locally while in flight and cooled down after failure
- certificate lock contention and stale order failures are emitted as structured certificate errors for automation

Verification sources:

- `packages/npmctl/tests/unit/test_planner.py`
- `packages/npmctl/tests/unit/test_apply.py`
- `packages/npmctl/tests/unit/test_repair_safe_certificates.py`
- `packages/npmctl/tests/integration/test_fake_npm_api.py`
