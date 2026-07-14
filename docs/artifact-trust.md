# Artifact trust and data handling

Artifacts use canonical SHA-256 semantic digests. Optional Ed25519 signatures bind that digest to a key identifier and signing time; environments may require signatures and maintain their own trusted-key set. Redaction removes configured sensitive fields before persistence or logging. Retention evaluation identifies expired artifacts but never deletes them automatically.
