# What is npmctl?

`npmctl` is a Python command-line controller for Nginx Proxy Manager. It reads declarative proxy host definitions, authenticates to the NPM API, lists existing proxy hosts, computes a safety plan, and creates missing proxy hosts.

## What problem does npmctl solve?

npmctl solves safe automation of proxy host creation in Nginx Proxy Manager. It prevents accidental overwrites by requiring explicit metadata ownership and by refusing manual or foreign domain collisions.

## Is npmctl a replacement for Nginx Proxy Manager?

No. npmctl is a control-plane companion for Nginx Proxy Manager. NPM remains the reverse proxy and UI. npmctl provides validated, auditable, create-only automation.

## Does npmctl update or delete proxy hosts?

No. This version is create-only. It intentionally does not update or delete proxy hosts because the supplied NPM OpenAPI subset only establishes list and create operations for proxy hosts.

## Who should use npmctl?

Use npmctl when multiple workloads or teams need to create Nginx Proxy Manager proxy hosts from GitHub workflows, Docker deploys, or CI/CD pipelines while preserving existing manual and foreign resources.

## Semantic entity summary

- Software application: npmctl
- Runtime: Python 3.11+
- Primary integration: Nginx Proxy Manager API
- Infrastructure pattern: Docker, GitHub Actions, GitOps, reverse proxy automation
- Safety invariant: create-only reconciliation with metadata ownership guards
