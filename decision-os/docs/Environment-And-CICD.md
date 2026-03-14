# Environment And CI/CD

## Environment Matrix

| Environment | Database             | Docker Tag | API URL        |
|-------------|----------------------|------------|----------------|
| Dev         | `decision_os_dev`    | `latest-dev` | `localhost`  |
| Staging     | `decision_os_staging`| `vX.X-rc`  | `staging.domain` |
| Prod        | `decision_os_prod`   | `vX.X`     | `api.domain` |

## Environment Files

- [.env.dev](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.env.dev)
- [.env.staging](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.env.staging)
- [.env.prod](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.env.prod)

## CI/CD Flow

`DEV -> PR -> Test -> Merge -> Build Docker -> Staging -> Manual Approval -> Prod`

Workflow file:

- [deploy.yml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/.github/workflows/deploy.yml)
