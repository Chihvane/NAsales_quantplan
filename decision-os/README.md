# Decision OS v3.0

Enterprise Quantitative Strategy & Governance Framework.

This repository is the enterprise-ready Python repository structure for `Decision OS v3.0`.

## Goals

- Extendable by layer
- Versioned by config and schema
- Runnable with minimal local setup
- Deployable in future via Docker or API service
- Friendly to multi-person collaboration

## Layer Map

`Field -> Metric -> Factor -> Model -> Gate -> Capital -> Portfolio -> Feedback`

## Repository Structure

- `docker/`: container and reverse-proxy deployment assets
- `config/`: runtime configuration
- `schemas/`: schema contracts
- `data/`: raw / processed / external placeholders
- `database/`: schema, seed, connection, migrations
- `backend/`: FastAPI service and decision engines
- `backend/oss_integrations/`: optional adapters for open-source tooling
- `backtest/`: walk-forward backtesting engine and reporting
- `worker/`: async task entrypoints
- `frontend/`: Streamlit operator views
- `report_engine/`: markdown and PDF reporting
- `tests/`: repository-level unit tests
- `notebooks/`: development notebooks

## Current Status

This repository now exposes a production-oriented structure:

- backend service layer
- authentication and role stubs
- decision / capital / portfolio modules
- docker assets
- database connection and schema scaffolding
- reporting layer
- walk-forward backtest layer
- optional OSS integration layer
- worker layer

Legacy `src/` remains as an earlier phase scaffold and can be retired once the `backend/` path fully replaces it.

## Production Blueprints Included

- Database ER design: [Database-ER-Design.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Database-ER-Design.md)
- Canonical schema: [schema.sql](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/database/schema.sql)
- Alembic template: [alembic.ini](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/alembic.ini)
- Environment files: [.env.dev](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.env.dev), [.env.staging](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.env.staging), [.env.prod](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.env.prod)
- CI/CD workflow: [deploy.yml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.github/workflows/deploy.yml)
- Backup and rollback scripts: [backup_db.sh](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/scripts/backup_db.sh), [rollback_release.sh](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/scripts/rollback_release.sh), [recover_portfolio.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/scripts/recover_portfolio.py)
- Schedule config: [schedule.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/schedule.yaml)
- Environment and CI/CD: [Environment-And-CICD.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Environment-And-CICD.md)
- Kubernetes blueprint: [Kubernetes-Deployment-Blueprint.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Kubernetes-Deployment-Blueprint.md)
- Observability and audit: [Observability-And-Audit.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Observability-And-Audit.md)
- Multi-tenant and permissions: [Multi-Tenant-And-Permissions.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Multi-Tenant-And-Permissions.md)
- API ingestion blueprint: [API-Ingestion-Blueprint.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/API-Ingestion-Blueprint.md)
- Disaster recovery: [Disaster-Recovery-And-Rollback.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Disaster-Recovery-And-Rollback.md)
- OSS integrations: [Open-Source-Integration-Blueprint.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Open-Source-Integration-Blueprint.md)
