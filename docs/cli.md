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
- `npmctl completion bash|powershell|zsh`: generate shell completion output.
- `npmctl audit-log`: read NPM audit log entries.
- `npmctl compliance artifacts --output-dir DIR`: generate SBOM, provenance, scan, and gate artifacts.
- `npmctl compliance gate --artifact-dir DIR`: fail closed when required compliance artifacts are missing or failing.
- `npmctl plugins list`: discover configured and entry-point plugin providers.

## Common options

- `--owner OWNER`: scope plan/apply/adopt to one owner.
- `--output text|json`: human or machine-readable output.
- `--no-updates`: turn owned drift into a conflict.
- `--prune-owned`: delete owned resources absent from desired state.
- `--config FILE`: load `[npmctl]` TOML configuration.
- `--validate-output`: validate plan output shape.
- `--backup-dir DIR`, `--report PATH`, `--rollback-plan PATH`, `--audit-log PATH`: write apply artifacts.
