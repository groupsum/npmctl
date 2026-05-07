# DNS records

npmctl schema v2 supports provider-backed DNS records through `dns_records`.
DNS records are declared with the same owner-scoped metadata contract as NPM
resources, so adoption and pruning can remain explicit and owner-scoped when DNS
apply support is enabled for a provider.

```yaml
apiVersion: npmctl.com/v1
schemaVersion: 2
dns_records:
  - provider: namecheap
    zone: npmctl.com
    type: A
    name: "@"
    value: 172.16.0.10
    ttl: 300
    meta:
      managed_by: npmctl
      owner: npmctl-lander
      resource_id: dns.npmctl-com.root-a
```

DNS provider inspection is available through:

```bash
npmctl plugins list
npmctl dns providers
npmctl dns doctor --provider namecheap
npmctl dns zones --provider namecheap
npmctl dns records --provider namecheap --zone npmctl.com
```
