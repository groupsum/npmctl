# npmctl-namecheap

Namecheap DNS provider extension for `npmctl`.

Install the package beside `npmctl`, then inspect discovery with:

```bash
npmctl plugins list
npmctl dns doctor --provider namecheap
```

Configuration is read from environment variables:

- `NAMECHEAP_API_USER`
- `NAMECHEAP_API_KEY`
- `NAMECHEAP_USERNAME`
- `NAMECHEAP_CLIENT_IP`
- `NAMECHEAP_API_BASE_URL` for tests or non-default endpoints
