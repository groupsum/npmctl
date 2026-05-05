# NPM deployment stack

This directory contains a SQLite-backed Nginx Proxy Manager stack for local use and CI. It deliberately avoids a separate database service.

```bash
docker compose -f deploy/npm/docker-compose.yml up -d
export NPM_BASE_URL=http://127.0.0.1:81/api
export NPM_IDENTITY=admin@example.com
export NPM_SECRET=changeme
uv run npmctl health
```

The CI compose file maps the admin UI/API to `http://127.0.0.1:8181/api`.
