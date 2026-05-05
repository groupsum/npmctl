# NPM Deployment Stack

This directory contains Docker Compose definitions for running Nginx Proxy Manager during local development and CI. The stack uses NPM's built-in SQLite storage and does not require a separate database service.

## Files

- `docker-compose.yml`: local development stack on the normal NPM ports
- `compose.ci.yml`: CI/E2E stack on alternate ports to avoid common local conflicts
- `env.example`: example environment values for local runs

## Local Development Stack

Start NPM on the standard ports:

```bash
docker compose -f deploy/npm/docker-compose.yml up -d
```

Ports:

- `80`: proxied HTTP traffic
- `81`: NPM admin UI and API
- `443`: proxied HTTPS traffic

Default bootstrap credentials:

```bash
export NPM_BASE_URL=http://127.0.0.1:81/api
export NPM_IDENTITY=admin@example.com
export NPM_SECRET=changeme
```

Check the API:

```bash
npmctl health
npmctl schema capabilities
```

The admin UI is available at `http://127.0.0.1:81`.

Stop the local stack:

```bash
docker compose -f deploy/npm/docker-compose.yml down
```

Remove local NPM volumes when you want a fresh instance:

```bash
docker compose -f deploy/npm/docker-compose.yml down -v
```

## CI/E2E Stack

The CI stack maps NPM to alternate ports:

- `8080`: proxied HTTP traffic
- `8181`: NPM admin UI and API
- `8443`: proxied HTTPS traffic

Start it locally:

```bash
docker compose -f deploy/npm/compose.ci.yml up -d
```

Configure npmctl:

```bash
export NPM_BASE_URL=http://127.0.0.1:8181/api
export NPM_IDENTITY=admin@example.com
export NPM_SECRET=changeme
```

Run the real NPM E2E suite:

```bash
export NPMCTL_REAL_NPM=1
uv run pytest --no-cov -m npm packages/npmctl/tests/e2e
```

Clean up:

```bash
docker compose -f deploy/npm/compose.ci.yml down
```

Use `down -v` only when you want to delete the test data volumes:

```bash
docker compose -f deploy/npm/compose.ci.yml down -v
```

## Running npmctl Against This Stack

Validate desired state:

```bash
uv run npmctl validate examples/desired-state
```

Plan one owner scope:

```bash
uv run npmctl plan examples/desired-state --owner workload-a
```

Apply one owner scope:

```bash
uv run npmctl apply examples/desired-state --owner workload-a
```

Prune resources owned by that owner but absent from desired state:

```bash
uv run npmctl apply examples/desired-state --owner workload-a --prune-owned
```

Adopt unmanaged matching resources:

```bash
uv run npmctl adopt examples/desired-state --owner workload-a
```

## Notes

- The bundled credentials are for disposable local and CI stacks. Change them for any persistent environment.
- NPM may take a few seconds to initialize after the container starts.
- `npmctl` treats resources without npmctl metadata as unmanaged until `adopt` is used.
