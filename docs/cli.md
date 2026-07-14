# CLI reference

## Commands

- `npmctl validate PATH`: validate desired state and metadata.
- `npmctl migrate PATH --check|--write`: check or write schema migrations.
- `npmctl schema fetch`: fetch `/schema` from NPM.
- `npmctl schema capabilities`: print endpoint capabilities.
- `npmctl schema check`: require proxy-host CRUD endpoints.
- `npmctl plan PATH`: compute side-effect-free plan.
- `npmctl apply PATH`: apply a clean plan.
- `npmctl adopt PATH`: explicitly adopt unmanaged matching resources.
- `npmctl drift PATH`: report remote drift without mutation.
- `npmctl doctor`: diagnose config, API reachability, and capabilities.
- `npmctl env`: show redacted environment diagnostics.
- `npmctl version --json`: show machine-readable package metadata.
- `npmctl contract list|show|check`: inspect independent contract compatibility.
- `npmctl repo validate|status`: validate a repository manifest and resolve an environment.
- `npmctl lock check EXPECTED ACTUAL`: compare reproducibility pins.
- `npmctl artifact inspect|digest`: validate and identify immutable artifacts.
- `npmctl completion bash|powershell|zsh`: generate shell completion output.
- `npmctl audit-log`: read NPM audit log entries.
- `npmctl compliance artifacts --output-dir DIR`: generate SBOM, provenance, scan, and gate artifacts.
- `npmctl compliance gate --artifact-dir DIR`: fail closed when required compliance artifacts are missing or failing.
- `npmctl plugins list`: discover configured and entry-point plugin providers.
- `npmctl dns providers`: list discovered DNS providers.
- `npmctl dns doctor --provider PROVIDER`: validate one DNS provider is loaded.
- `npmctl dns zones --provider PROVIDER`: list zones for one DNS provider.
- `npmctl dns records --provider PROVIDER --zone ZONE`: list records for one DNS provider zone.

## Common options

- `--owner OWNER`: scope plan/apply/adopt to one owner.
- `--output text|json`: human or machine-readable output.
- `--no-updates`: turn owned drift into a conflict.
- `--prune-owned`: delete owned resources absent from desired state.
- `--config FILE`: load `[npmctl]` TOML configuration.
- `--validate-output`: validate plan output shape.
- `--backup-dir DIR`, `--report PATH`, `--rollback-plan PATH`, `--audit-log PATH`: write apply artifacts.

## Reviewed artifacts

Use `npmctl plan PATH --artifact-out PLAN --repository ORG/REPO
--environment production --commit SHA` to persist exact ordered operations.
Apply the reviewed result with `npmctl apply --artifact PLAN` and the same
binding values. Changed commits, live state, NPM API profiles, environments,
repositories, or expiry timestamps fail before
mutation.
