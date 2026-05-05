# Desired-state schema

Desired state requires `apiVersion: npmctl.io/v1` and `schemaVersion: 1`. Resource lists are `certificates`, `access_lists`, and `proxy_hosts`.

Every managed resource requires metadata:

```yaml
meta:
  managed_by: npmctl
  owner: workload-a
  resource_id: proxy.app
```

`resource_id` is the stable identity. Domain names and names are natural keys used for collision detection.
