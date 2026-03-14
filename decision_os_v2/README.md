# Decision OS v2.0

`Decision OS v2.0` is the runtime-oriented upgrade of the existing report stack.

It standardizes the full decision chain as:

`Field -> Metric -> Factor -> Model -> Gate -> Capital -> Portfolio -> Feedback`

## Scope

- Registry templates: [registry](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry)
- Runtime engine: [gate_engine_v2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/gate_engine_v2.py)
- Capital allocator: [capital_allocator.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/capital_allocator.py)
- Feedback engine: [feedback_engine.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/feedback_engine.py)
- Demo runner: [demo.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/demo.py)

## Key Files

- System document: [Decision-OS-v2.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v2.0.md)
- Architecture: [Decision-OS-v2.0-Architecture.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v2.0-Architecture.md)
- Demo output: [decision_os_v2_demo.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_decision_os_v2/decision_os_v2_demo.json)

## Run

```bash
python3 examples/run_decision_os_v2_demo.py
```

## Notes

- JSON registry loading works without optional dependencies.
- YAML registry loading uses `PyYAML`, which is already declared in [requirements.txt](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/requirements.txt).
