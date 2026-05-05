# SSL certificate CRUD

npmctl models certificates as owner-scoped resources. Because NPM certificate payloads vary by DNS provider and API version, certificate declarations support an `api_payload` pass-through merged with `name`, `domain_names`, `certificate_type`, and managed metadata.

Proxy hosts should reference certificates by `certificate_ref` whenever the certificate is declared in the same desired state.
