# NAsales_quantplan

北美小众兴趣商品量化研究与 `Decision OS` 决策系统工程仓。

这个仓库已经不是单一研究报告模板，而是两条主线并行的系统：

- `quant_framework`：Part 0-5 量化研究、报告生成、图表、清洗、回测。
- `decision-os`：企业级 `Decision OS` 工程骨架，覆盖 Gate、资本、风险、组合、回测、部署蓝图。

## 项目目标

面向北美特定兴趣商品类目，建立一套可复用、可量化、可回测、可审计、可决策的研究与经营系统。

覆盖范围包括：

- `Part 0`：研究治理与决策总则
- `Part 1`：市场量化研究与进入判断
- `Part 2`：商品画像、竞争结构与成交分析
- `Part 3`：中国供应链、出口流程与 landed cost
- `Part 4`：北美渠道、投放与 ROI 可行性
- `Part 5`：上线后经营、实验、风控与资本配置
- `Horizontal System`：主数据、证据链、审计链、规则控制塔
- `Decision OS`：Field -> Metric -> Factor -> Model -> Gate -> Capital -> Portfolio -> Feedback

## 仓库结构

- [quant_framework](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework)：量化研究主代码
- [decision-os](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os)：生产级工程骨架
- [decision_os_mvp](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_mvp)：最小可运行 MVP
- [decision_os_ui](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_ui)：Dashboard 与自动报告系统
- [examples](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples)：各 Part demo 输入、脚本、输出
- [artifacts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/artifacts)：桥接、最终报告、回测产物
- [docs](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs)：总索引与 Part README
- [tests](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/tests)：`quant_framework` 回归测试

## 建议阅读顺序

如果你第一次看这个仓库，按这个顺序：

1. 统一链条索引：[README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-chains/README.md)
2. 总索引：[Part1-5-Workspace-Index.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/Part1-5-Workspace-Index.md)
3. 系统契约：[Quant-Report-Contract.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Quant-Report-Contract.md)
4. `Decision OS` 白皮书：
   [Decision-OS-v3.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v3.0.md)
   [Decision-OS-v3.0-Dashboard-Spec.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v3.0-Dashboard-Spec.md)

## 两条主线

### 1. 研究与量化主线

入口：

- [part0.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0.py)
- [part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
- [part2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2.py)
- [part3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3.py)
- [part4.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4.py)
- [part5.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5.py)
- [cli.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/cli.py)

这条线负责：

- 标准输入表定义
- 指标计算
- 因子快照
- 图表生成
- 清洗模板
- demo 与章节报告
- Part 级回测

### 2. Decision OS 工程主线

入口：

- [decision-os/README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/README.md)
- [decision-os/backend](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/backend)
- [decision-os/backtest](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/backtest)
- [decision-os/database/schema.sql](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/database/schema.sql)

这条线负责：

- Gate Engine
- 资本池与风险预算
- Portfolio 分配
- Walk-forward backtesting
- 生产部署蓝图
- 多租户、审计、权限、SaaS 化设计

## 当前关键成果

- `Part 0-5 + Horizontal System` 已全部具备：
  - 文档
  - 量化结构
  - 代码入口
  - demo 输入
  - demo 输出
  - validation
- `Part 1` 已升级为 `Market Quant Engine` 候选，支持：
  - `event_library`
  - `source_registry`
  - `threshold_registry`
  - `factor_snapshots`
- `Part 2` 已输出商品竞争与成交因子
- `Part 1 + Part 2` 已打通到 `Decision OS`，桥接产物在：
  - [integrated_market_product_bundle.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/artifacts/decision_os_bridge/integrated_market_product_bundle.json)
  - [integrated_factor_panel.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/artifacts/decision_os_bridge/integrated_factor_panel.csv)
- `Decision OS` 已有：
  - 工程仓结构
  - 数据库 schema
  - ORM
  - repository 层
  - backtest 引擎
  - UI 原型

## 快速开始

### 环境

安装根依赖：

```bash
python3 -m pip install -r requirements.txt
```

如果你要跑 `decision-os` 生产骨架相关代码，再安装它自己的依赖。

### 跑 Part 1-5 demo

```bash
python3 examples/run_part0_demo.py
python3 examples/run_part1_demo.py
python3 examples/run_part2_demo.py
python3 examples/run_part3_demo.py
python3 examples/run_part4_demo.py
python3 examples/run_part5_demo.py
```

### 跑桥接 demo

```bash
python3 examples/run_decision_os_bridge_demo.py
```

### 跑 Decision OS demo

```bash
python3 examples/run_decision_os_v3_demo.py
python3 decision-os/scripts/run_backtest_demo.py
python3 decision-os/scripts/run_backtest_optimization.py
```

### 跑 UI

```bash
python3 -m uvicorn decision_os_ui.backend.main:app --reload
python3 -m streamlit run decision_os_ui/frontend/app.py
```

## 测试

根测试：

```bash
python3 -m unittest discover -s tests -v
```

`decision-os` 测试：

```bash
python3 -m unittest discover -s decision-os/tests -v
```

## 典型输出位置

- Part 1 输出：[examples/output](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output)
- Part 2 输出：[examples/output_part2](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part2)
- Part 3 输出：[examples/output_part3](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part3)
- Part 4 输出：[examples/output_part4](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part4)
- Part 5 输出：[examples/output_part5](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part5)
- 最终 PDF / 可视化：[artifacts/final_report](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/artifacts/final_report)
- `Decision OS` 回测产物：[decision-os/artifacts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/artifacts)

## 当前最值得继续的方向

按当前系统状态，最直接的下一步是：

1. 用 `Part 3 / Part 4` 的真实成本与渠道费率替换桥接层里的 `proxy` 字段
2. 把桥接 bundle 直接接入 `decision-os/backtest`
3. 用真实历史快照替换 demo panel，做完整 walk-forward 与 stress test

## 参考入口

- 总索引：[Part1-5-Workspace-Index.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/Part1-5-Workspace-Index.md)
- `Decision OS` 白皮书：[Decision-OS-v3.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v3.0.md)
- `Decision OS` 工程仓：[decision-os](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os)
- `Decision OS UI`：[decision_os_ui](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_ui)
