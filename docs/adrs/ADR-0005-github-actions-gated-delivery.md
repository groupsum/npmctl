# ADR-0005: GitHub Actions gated delivery

Status: accepted

CI, docs/SSOT, Python Matrix, Live NPM Gate, and release are separate gated flows with concurrency controls.
The dispatchable release flow starts CI, Docs/SSOT, Python Matrix, and Live NPM Gate for the selected ref, requires all to succeed, and only then performs selected GitHub Release and PyPI publication actions.
