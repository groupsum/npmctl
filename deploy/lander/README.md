# npmctl.com Lander

Static placeholder lander for `npmctl.com` and `www.npmctl.com`.

Deploy from the repository root:

```bash
docker compose -f deploy/lander/compose.yml up -d --build
```

The container is explicitly named `npmctl_lander` and listens on port 80 inside
the `npmctl_lander_net` Docker network.
