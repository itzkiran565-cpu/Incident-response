from agent import log_incident, log_outcome_feedback

# payments-api — recurring pattern (3 incidents, same root cause)
payments_incidents = [
    ("2026-06-15", "p99 latency spike, 5xx rate 12%, TimeoutError: connection pool exhausted after 30000ms",
     "connection leak in retry logic introduced by deploy #482", "rolled back deploy #482", 34, "runbook-db-pool-exhaustion.md"),
    ("2026-06-29", "connection pool exhausted, timeouts on checkout flow, TimeoutError after 30000ms",
     "same retry logic leak reintroduced in deploy #490", "rolled back deploy #490", 28, "runbook-db-pool-exhaustion.md"),
    ("2026-07-10", "500 errors spiking, TimeoutError: connection pool exhausted, checkout affected",
     "deploy #501 reused old retry code path", "rollback + hotfix PR #503", 19, "runbook-db-pool-exhaustion.md"),
    ("2026-07-02", "high latency, 200s succeeding but slow, no pool exhaustion",
     "downstream fraud-check-service degraded, p99 4.2s", "enabled circuit breaker on fraud-check-service", 41, "runbook-downstream-timeout.md"),
]

# auth-service — different pattern (proves the agent generalizes, not just one rigged demo)
auth_incidents = [
    ("2026-06-20", "auth failures spiking across all endpoints, 401 rate 30%",
     "internal TLS cert for auth-service expired", "renewed cert, added 30-day expiry monitor", 15, "runbook-cert-expiry.md"),
    ("2026-07-18", "auth failures again, 401 rate 25%, same pattern as before",
     "renewal automation script silently failed, cert expired again", "renewed cert manually, fixed automation script bug", 22, "runbook-cert-expiry.md"),
]

for date, symptoms, cause, fix, mins, runbook in payments_incidents:
    log_incident("payments-api", date, symptoms, cause, fix, mins, runbook)
    print(f"[payments-api] {date}: {cause}")

for date, symptoms, cause, fix, mins, runbook in auth_incidents:
    log_incident("auth-service", date, symptoms, cause, fix, mins, runbook)
    print(f"[auth-service] {date}: {cause}")

# Outcome feedback example — proves the learning loop
log_outcome_feedback(
    "payments-api",
    "connection leak in retry logic",
    "rollback + hotfix PR #503",
    worked=True
)

log_outcome_feedback(
    "payments-api",
    "downstream fraud-check-service degraded",
    "enable circuit breaker",
    worked=True
)

log_outcome_feedback(
    "auth-service",
    "internal TLS cert expired",
    "renew certificate manually",
    worked=True
)

print("\nSeeding complete.")
print("payments-api: 3 incidents share the connection-pool-exhaustion pattern (recurrence demo)")
print("auth-service: 2 incidents share the cert-expiry pattern (generalization proof)")
