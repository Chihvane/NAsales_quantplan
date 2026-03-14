# Decision OS v3.0

`Decision OS v3.0` is the enterprise-grade rewrite of the research stack into a governed runtime system.

It standardizes the full operating chain as:

`Field -> Metric -> Factor -> Model -> Gate -> Capital -> Portfolio -> Feedback`

## Included

- Whitepaper: [Decision-OS-v3.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v3.0.md)
- Dashboard spec: [Decision-OS-v3.0-Dashboard-Spec.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v3.0-Dashboard-Spec.md)
- Runtime package: [decision_os_v3](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3)
- Database schema: [decision_os_v3_schema.sql](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/db/decision_os_v3_schema.sql)

## Runtime Modules

- Gate runtime: [gate_engine_v3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/gate_engine_v3.py)
- Portfolio allocator: [portfolio_engine.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/portfolio_engine.py)
- Feedback engine: [feedback_engine.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/feedback_engine.py)
- Registry loader: [registry_loader.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/registry_loader.py)
- Demo runner: [demo.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/demo.py)

## Registry

- System config: [system.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/registry/system.yaml)
- Capital config: [capital_pool.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/registry/config/capital_pool.yaml)
- Risk config: [risk_budget.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/registry/config/risk_budget.yaml)
- Gate example: [gate_market_entry.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v3/registry/examples/gate_market_entry.yaml)

## Run

```bash
python3 examples/run_decision_os_v3_demo.py
```
