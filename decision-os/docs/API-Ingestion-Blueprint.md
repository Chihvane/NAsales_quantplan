# API Ingestion Blueprint

## Source Connectors

- Amazon SP-API
- Google Trends
- Statista
- Keepa

## Data Flow

`External API -> Raw DB -> Clean DB -> Factor Engine -> Model Engine -> Gate Engine`

## Scheduled Jobs

Defined in [schedule.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/schedule.yaml)

## Stub Connectors

- [amazon_sp.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/backend/api_connectors/amazon_sp.py)
- [google_trends.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/backend/api_connectors/google_trends.py)
- [tasks_market.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/worker/tasks_market.py)
