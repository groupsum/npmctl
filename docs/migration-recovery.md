# Migration recovery

Migrations declare either `reversible` or `forward-repair-only`. Rollback is available only when a verified inverse exists. Otherwise npmctl compares the reviewed expected snapshot with observed state and produces an explicit repair plan. Lease tokens prevent stale executors from renewing or releasing another executor's scope.
