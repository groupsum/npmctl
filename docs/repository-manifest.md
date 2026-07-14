# Repository manifest

`.npmctl/repository.yaml` is a schema-1 `NpmctlRepository`. It binds repository identity, owners, domains, environments, and desired-state inputs. References must resolve to files inside `.npmctl`, which prevents one environment from accidentally consuming another repository's configuration.

Use `npmctl repo validate .npmctl/repository.yaml` and `npmctl repo status .npmctl/repository.yaml --environment production`.
