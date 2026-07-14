# npmctl versioning and migration test plan

Status: partially implemented and passing

The npmctl 0.4 verification suite implements the contract, artifact, schema
migration, transaction, ledger, recovery, repository, signing, redaction,
retention, provider-capability, and local-lease cases below. The complete suite
passes with 100% statement and branch coverage. Tests that remain `planned` in
the SSOT registry identify the intentionally deferred work: durable resume and
external-effect idempotency, shared-runner complete-zone locking, full plugin
version negotiation, and universal versioned CLI error envelopes.

Implemented test locations:

- `packages/npmctl/tests/unit/test_contract_versions.py`
- `packages/npmctl/tests/unit/test_plan_artifacts.py`
- `packages/npmctl/tests/unit/test_migration_graph.py`
- `packages/npmctl/tests/unit/test_cli_versioning.py`
- `packages/npmctl/tests/unit/test_loader_migrations.py`

## Contract versioning

- `tst:contract-version-matrix`: exercise every supported read/write contract
  version and reject unsupported write targets.
- `tst:contract-future-version-rejection`: reject unknown future versions
  without mutating input.
- `tst:contract-deprecation-policy`: verify warnings, strict failures, and
  machine-readable lifecycle metadata.
- `tst:canonical-digest-stability`: prove equivalent YAML serializations have
  the same digest and semantic changes do not.
- `tst:lockfile-reproducibility`: reproduce identical resolved inputs from a
  lockfile and reject mismatched pins.

## Immutable planning and execution

- `tst:plan-artifact-roundtrip`: validate and round-trip the PlanArtifact
  schema without losing identity fields.
- `tst:plan-artifact-tamper-rejection`: reject any post-review artifact change.
- `tst:plan-artifact-staleness`: reject changed source, desired-state, target,
  live-state, and expired artifacts.

## Migration engine

- `tst:migration-step-matrix`: exercise adjacent and composed migration paths.
- `tst:migration-manifest-schema`: validate scope, policy, checkpoints,
  recovery, and source/target identity.
- `tst:migration-atomic-failure`: inject failures before and during replacement
  and prove no partial repository rewrite remains.
- `tst:migration-ledger-append-only`: reject mutation or truncation of recorded
  migration history.
- `tst:migration-resume`: resume from each durable checkpoint without repeating
  completed external effects.
- `tst:migration-verification`: validate target contracts and provider readback.

## Live-resource migrations

- `tst:live-state-classification`: classify owned, matching unmanaged, drifting
  unmanaged, foreign-owned, and ambiguous resources.
- `tst:migration-adoption-gates`: require an exact scoped manifest and approval.
- `tst:ownership-transfer`: require consistent source and destination ownership
  evidence.
- `tst:migration-delete-gates`: require explicit scope, approval, snapshot, and
  verification for prune and delete.
- `tst:apply-rejects-migration-operations`: prove ordinary apply cannot adopt,
  transfer, prune, or delete without a migration artifact.

## Provider and target compatibility

- `tst:provider-capability-matrix`: validate capability contracts for every
  supported provider.
- `tst:unsupported-provider-capability`: fail closed before mutation.
- `tst:npm-api-profile-drift`: reject a target profile that changed after plan.
- `tst:complete-zone-concurrency`: serialize complete-zone writes and re-plan
  while holding the zone lock.

## Recovery

- `tst:migration-reversibility-classification`: require an explicit recovery
  classification.
- `tst:reversible-migration-rollback`: verify the declared inverse restores the
  prior state.
- `tst:irreversible-migration-rejects-rollback`: refuse false rollback claims.
- `tst:forward-repair-from-snapshot`: derive and verify repair from the complete
  prechange snapshot and ledger checkpoints.

## Repository contract

- `tst:repository-manifest-validation`: validate repository identity, domains,
  environments, modes, and desired-state roots.
- `tst:repository-layout-validation`: reject missing, misplaced, or ambiguously
  versioned `.npmctl` files.
- `tst:repository-cross-environment-isolation`: reject references that cross
  environment or ownership boundaries.

## Explicit migration boundaries

- `tst:validate-never-migrates`: prove validation cannot rewrite an older
  readable contract.
- `tst:plan-never-migrates`: prove planning cannot rewrite source contracts.
- `tst:apply-never-migrates`: prove ordinary apply cannot rewrite source
  contracts as a side effect.
- `tst:safe-downgrade-roundtrip`: verify a declared reversible downgrade and
  its forward round trip preserve the contract meaning.
- `tst:irreversible-downgrade-rejection`: reject downgrade when no verified
  inverse exists.

## Artifact authenticity and data safety

- `tst:artifact-valid-signature`: accept a trusted signature over the canonical
  artifact identity.
- `tst:artifact-invalid-signature`: reject tampered or malformed signatures.
- `tst:artifact-untrusted-signer`: reject a valid signature from an untrusted
  or revoked key.
- `tst:artifact-secret-redaction`: prove plans, reports, logs, and errors never
  expose configured secret fields.
- `tst:snapshot-sensitive-field-omission`: prove snapshots persist only fields
  allowed by their artifact policy.
- `tst:artifact-retention-expiry`: enforce artifact expiry and disposal policy.

## Migration concurrency and idempotency

- `tst:concurrent-migration-rejection`: prevent two executors from mutating the
  same migration scope concurrently.
- `tst:migration-lease-expiry`: exercise safe expiry, takeover, and stale-owner
  rejection.
- `tst:duplicate-operation-idempotency`: prove repeated operation identity does
  not duplicate an external effect.
- `tst:provider-response-loss`: reconcile an ambiguous provider result through
  readback before retry.
- `tst:resume-after-provider-success`: resume after a successful external write
  whose response was lost without repeating it.

## Plugin contract migration

- `tst:plugin-supported-contract-version`: negotiate a supported plugin
  contract range.
- `tst:plugin-future-schema-rejection`: reject unsupported future plugin and
  custom-resource schemas.
- `tst:plugin-migration-discovery`: discover and compose registered adjacent
  plugin migration steps.
- `tst:plugin-migration-path-conflict`: reject ambiguous or duplicate migration
  paths.
- `tst:plugin-missing-migration-step`: fail before mutation when a required
  plugin step is missing.

## Deterministic planning and CLI automation

- `tst:repeated-plan-determinism`: produce identical semantic artifacts and
  digests from identical desired and live state.
- `tst:operation-order-determinism`: maintain canonical operation ordering
  independently of provider response ordering.
- `tst:cli-versioned-error-envelope`: verify every machine-readable failure
  uses the declared CommandResult schema and semantic code.
- `tst:cli-versioned-exit-code-matrix`: verify stable exit codes, mutation
  indicators, and retryability across command families.
