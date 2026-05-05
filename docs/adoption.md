# Adoption

`npmctl adopt` is used to bring manual NPM resources under declarative management. Default adoption is strict: the unmanaged resource must match desired fields before metadata is written.

Use `--allow-field-drift` or `--force` only when intentionally claiming and overwriting unmanaged state.
