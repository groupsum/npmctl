# Compliance Artifacts

npmctl can generate release-adjacent compliance artifacts for CI or local
certification work:

```powershell
uv run npmctl compliance artifacts --output-dir dist/compliance
uv run npmctl compliance gate --artifact-dir dist/compliance
```

The command writes:

- `sbom.spdx.json`
- `provenance.intoto.json`
- `security-scan.json`
- `dependency-vulnerability.json`
- `release-gates.json`

These artifacts provide a stable governed surface for SBOM, provenance,
security-scan, dependency-vulnerability, and release-gate evidence.

The gate command fails closed unless every required artifact exists, parses as
JSON, reports a passing status, and contains the expected release-gate
aggregation. CI and release builds use this command so certification cannot rely
on placeholder success files.
