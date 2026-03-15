# Part 1 / Part 2 / Decision OS Bridge

更新时间：2026-03-15

## 本轮打通内容

当前工作区原本存在两条并行链：

- `quant_framework/` 负责 Part 1–5 的量化报告与图表
- `decision-os/` 负责 Gate、资本、回测与生产级接口

本轮新增桥接层后，`Part 1 + Part 2` 已经可以直接导出给 `Decision OS` 消费。

## 已新增对象

### Part 2 因子快照

`Part 2` 现在输出：

- `FAC-COMPETITION-HEADROOM`
- `FAC-PRICING-FIT`
- `FAC-WHITESPACE-DEPTH`
- `FAC-SHELF-STABILITY`

### 跨系统桥接模块

新增模块：

- `quant_framework/decision_os_bridge.py`

输出产物：

- `integrated_market_product_bundle.json`
- `integrated_factor_panel.csv`

## Bundle 内容

桥接 bundle 当前包含：

- `tenant_id`
- `as_of_date`
- `report_refs`
- `field_data_proxy`
- `gate_inputs`
- `proxy_flags`
- `factor_panel`

其中 `field_data_proxy` 会把 Part 1 / Part 2 的报告结果映射为 `Decision OS` 需要的最小输入：

- `TAM`
- `CAGR`
- `HHI`
- `volatility`
- `expected_price`
- `landed_cost`
- `platform_fee`

## 当前限制

由于 Part 1 / Part 2 本身不产出真实 landed cost，本轮桥接仍使用：

- `landed_cost_proxy`
- `platform_fee_proxy`

这些代理已经显式记录在 `proxy_flags` 中，后续应由 Part 3 / Part 4 的真实成本与费率替换。

## Decision OS 侧效果

`decision-os/backend/dependencies.py` 现在会优先读取：

- `artifacts/decision_os_bridge/integrated_market_product_bundle.json`

如果 bundle 存在，则：

- API 不再只使用 `sample_market_fields`
- `/market/factor`
- `/model/simulation`
- `/gate/status`

都会优先使用 Part 1 / Part 2 导出的桥接输入

## 下一步

下一轮最值的是：

1. 用 Part 3 landed cost 替换 `landed_cost_proxy`
2. 用 Part 4 channel fee / CAC 替换 `platform_fee_proxy`
3. 把 bridge bundle 接入 `decision-os/backtest`，替换 demo panel 的手工字段

## 本轮联网校对的官方参考

- Google Trends 帮助文档：
  [Google Trends Help](https://support.google.com/trends/answer/4365533)
- GX Core 官方文档：
  [GX Core Introduction](https://docs.greatexpectations.io/docs/core/introduction/)
- Evidently 官方文档：
  [Evidently Docs](https://docs.evidentlyai.com/)
- MLflow 官方文档：
  [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- Optuna 官方文档：
  [Optuna Documentation](https://optuna.readthedocs.io/en/stable/)
