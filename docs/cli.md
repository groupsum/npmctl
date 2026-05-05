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

## Common options

- `--owner OWNER`: scope plan/apply/adopt to one owner.
- `--output text|json`: human or machine-readable output.
- `--no-updates`: turn owned drift into a conflict.
- `--prune-owned`: delete owned resources absent from desired state.
