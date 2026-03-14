# SaaS Multi-Tenant Upgrade Architecture

## Target
Upgrade Decision OS from a single-workspace deployment into a shared SaaS platform that supports multiple brands, markets, and tenant-specific rule sets without breaking auditability.

## Isolation Strategy
Recommended baseline: shared PostgreSQL cluster, shared schema, row-level isolation by `tenant_id`.

Every query and write path must enforce:

```sql
WHERE tenant_id = :current_tenant_id
```

### When to upgrade isolation
- Use schema-per-tenant when one tenant requires custom database extensions, dedicated retention rules, or large-volume workload isolation.
- Use database-per-tenant only for regulated customers that require network or storage separation.

## Tenant-Aware Service Boundaries
- `backend/api/*`: resolve tenant from JWT claims and inject into request scope.
- `backend/repositories/*`: all reads and writes are tenant-filtered by default.
- `backend/audit/*`: every log record includes `tenant_id`, `user_id`, and immutable hashes.
- `report_engine/*`: reports are generated under tenant-specific paths and versions.

## Control Points
- JWT claims must contain `tenant_id`, `role`, and expiration.
- Repository layer must reject cross-tenant reads unless an explicit admin override is present.
- Gate approvals above a configurable threshold should require dual approval for `strategy_director` + `risk_officer`.

## SaaS Upgrade Roadmap
1. Introduce tenant-aware repositories and request-scoped tenant resolution.
2. Add PostgreSQL row-level security policies.
3. Add tenant-scoped config registry for gates, capital, and risk budgets.
4. Add tenant metering, billing, and feature flags.
5. Add tenant-specific data retention and export tooling.

## Shared vs Tenant-Specific Configuration
- Shared: system schema versions, common audit format, API connector framework.
- Tenant-specific: gate thresholds, capital pools, risk budgets, allowed channels, approval matrix.

## Example Request Flow
1. User signs in and receives JWT with `tenant_id`.
2. API dependency resolves `tenant_id`.
3. Repository layer automatically scopes the session query.
4. Gate decision writes `tenant_id` to `decision_log` and `audit_log`.
5. Feedback loop recalibrates only tenant-specific models unless a shared global model is explicitly configured.
