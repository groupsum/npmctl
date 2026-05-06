# Operational Hardening

npmctl apply operations can now emit explicit operational artifacts:

- `--backup-dir DIR` writes the pre-apply remote state.
- `--report PATH` writes a structured transaction report.
- `--rollback-plan PATH` writes best-effort rollback instructions.
- `--audit-log PATH` writes a local audit record for the apply command.

Operators can inspect drift without mutation:

```powershell
uv run npmctl drift examples/desired-state --output json
```

The `audit-log` command reads NPM audit log entries through the API:

```powershell
uv run npmctl --base-url http://npm.local/api --identity admin@example.com --secret *** audit-log --since 24h
```
