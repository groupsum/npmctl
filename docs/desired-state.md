# Desired-state schema

Desired state requires `apiVersion: npmctl.com/v1` and `schemaVersion: 1`.
Resource lists are `certificates`, `access_lists`, `proxy_hosts`,
`redirection_hosts`, `dead_hosts`, `streams`, `users`, `settings`,
`plugin_resources`, and `external_certificates`.

Every managed resource requires metadata:

```yaml
meta:
  managed_by: npmctl
  owner: workload-a
  resource_id: proxy.app
```

`resource_id` is the stable identity. Domain names and names are natural keys used for collision detection.

Additional resource kinds use pass-through `api_payload` fields while keeping
the same owner metadata contract:

```yaml
redirection_hosts:
  - domain_names: [old.example.com]
    forward_domain_name: new.example.com
    meta: {managed_by: npmctl, owner: workload-a, resource_id: redir.old}
streams:
  - incoming_port: 5432
    forward_host: db
    forward_port: 5432
    protocol: tcp
    meta: {managed_by: npmctl, owner: workload-a, resource_id: stream.db}
```

Runtime plugin providers can contribute desired resources without bypassing the
owner metadata contract. A resource provider is selected by name and converts a
provider-specific payload into one supported generic NPM resource kind:

```yaml
plugin_resources:
  - provider: stream-provider
    payload:
      incoming_port: 15432
      owner: workload-a
      resource_id: stream.plugin-db
```

Certificate providers can resolve external references into certificate payloads.
The resolved payload is still parsed as a normal managed certificate:

```yaml
external_certificates:
  - provider: vault-certificates
    reference: prod/example
    name: prod-example
    domain_names: [example.com]
    meta: {managed_by: npmctl, owner: workload-a, resource_id: cert.example}
```
