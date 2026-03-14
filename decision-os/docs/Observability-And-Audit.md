# Observability And Audit

## Logging Path

`Application -> Logstash -> Elasticsearch -> Kibana`

## Standard Log Shape

```json
{
  "timestamp": "",
  "module": "",
  "entity_id": "",
  "action": "",
  "user": "",
  "version": "",
  "decision_id": ""
}
```

## Grafana Metrics

- API latency
- Gate trigger frequency
- Capital utilization
- Risk exposure
- Monte Carlo runtime

## Audit Rule

Audit records are append-only and must not be deleted.
