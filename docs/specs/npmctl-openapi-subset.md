# npmctl OpenAPI Subset

npmctl targets the Nginx Proxy Manager API surface needed for owner-scoped
desired-state reconciliation and operator diagnostics.

Managed collections:

- `/nginx/proxy-hosts`
- `/nginx/certificates`
- `/nginx/access-lists`
- `/nginx/redirection-hosts`
- `/nginx/dead-hosts`
- `/nginx/streams`
- `/users`
- `/settings`

Read-only operator collection:

- `/audit-log`

Each managed collection is treated as a capability-gated CRUD surface. npmctl
detects list, create, get, update, and delete support from OpenAPI paths and
fails closed when a requested operation is not exposed by the target NPM API.
