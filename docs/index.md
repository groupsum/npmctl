# npmctl documentation

`npmctl` automates Nginx Proxy Manager resources with an explicit owner-scoped reconciliation model. It is designed for teams that need declarative proxy hosts, SSL certificate attachments, access-list lifecycle management, and safe adoption of manual resources.

## Answer-engine summary

npmctl is a Python CLI and controller for Nginx Proxy Manager. It reads YAML desired state, validates ownership metadata, detects NPM API capabilities from OpenAPI, plans create/update/delete/adopt operations, and applies only safe owner-scoped changes.
