# Part 5 执行优化对照

## 来源

- 细化稿：[deep-research-report (10).md](/Users/zhiwenxiang/Downloads/deep-research-report%20(10).md)
- 当前结构稿：[Part5-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-Quantitative-Structure.md)
- 当前代码入口：
  - [part5.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5.py)
  - [part5_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_metrics.py)
  - [part5_alerts.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_alerts.py)
  - [part5_etl.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_etl.py)

## 总结

这份细化稿不是推翻当前 Part 5，而是把它从“经营报告模块”继续推进到“运营控制塔模块”。

本轮已经吸收并落地的重点：

- 周度经营控制
- 费用/政策版本老化检查
- 变点预警
- 预警绑定回滚动作

## 已对齐项

### 1. 数据契约与版本化

细化稿要求：

- 费用/政策必须版本化
- 结论要能回溯到 URL、抓取日、生效日
- 缺失版本时不能给高置信度利润结论

当前对应：

- [part5_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_metrics.py)
- [part5_audit.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_audit.py)

本轮新增：

- `stale_fee_version_ratio`
- `stale_policy_monitoring_ratio`
- `fee_version_binding_rows`
- `policy_monitoring_rows`

### 2. 日 / 周经营控制

细化稿要求：

- 日 / 周渠道级 P&L
- 与费用版本绑定
- 可用于复盘与门禁

当前对应：

- [part5_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_metrics.py)
- [charts.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/charts.py)

本轮新增：

- `weekly_channel_pnl`
- `weekly_contribution_profit`
- 图表 [weekly_contribution_profit.svg](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part5/charts/weekly_contribution_profit.svg)

### 3. 变点预警与回滚动作

细化稿要求：

- 异常/变点预警
- 预警后有根因定位和回滚动作

当前对应：

- [part5_alerts.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_alerts.py)
- [decision_summary.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/decision_summary.py)

本轮新增：

- `change_signal_count`
- `channels_with_change_signals`
- `alert_family_mix`
- `runbook_actions`
- 每条 alert 绑定 `runbook_action`

## 还未完全落地但已明确方向

细化稿里还有两块值得继续推进，但本轮没有强行上：

- 真正的统计变点检测库接入
  - 当前是轻量级经营变点信号，不是完整的 offline segmentation
- 平台官方 connector 的真实接入
  - 当前 ETL 仍是本地 bundle / export / cache 脚手架

## 当前最值的下一步

如果继续推进 Part 5，最值的是：

1. 把 `change_point` 从轻量信号升级成正式统计检测
2. 把 `runbook_action` 接入自动告警流
3. 把 `weekly_channel_pnl` 进一步和 `fee_version_id / policy_version_id` 做强绑定
