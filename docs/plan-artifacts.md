# Immutable plan artifacts

`npmctl plan DESIRED --artifact-out plan.yaml` records exact ordered NPM
resource operations plus the source commit, repository, environment,
desired-state digest, live-state fingerprint, and NPM API profile. `npmctl apply
--artifact plan.yaml` rejects expired, conflicting, stale, or differently bound
plans before mutation. DNS execution artifacts remain planned; npmctl fails
artifact creation when the desired state contains DNS records instead of
silently omitting those operations.

Adoption and deletion are deliberately excluded from ordinary plan artifacts; those actions require a reviewed migration manifest.
