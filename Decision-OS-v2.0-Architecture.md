# Decision OS v2.0 Architecture

```mermaid
flowchart TD
  F["Field Layer\nsource / unit / confidence / validation"]
  M["Metric Layer\nformula / depends_on / aggregation"]
  FAC["Factor Layer\nweights / normalization / decision abstraction"]
  MOD["Model Layer\nsimulation / forecast / optimization / causal"]
  G["Gate Layer\nGo / No-Go / Scale / Exit"]
  C["Capital Layer\npool / free capital / capital cost"]
  P["Portfolio Layer\nallocation / concentration / prioritization"]
  FB["Feedback Layer\nactuals / error / recalibration"]

  F --> M
  M --> FAC
  FAC --> MOD
  MOD --> G
  C --> G
  G --> P
  P --> FB
  FB --> MOD
```

## 关系说明

- `Field -> Metric -> Factor -> Model` 是计算链
- `Capital -> Gate` 是硬约束链
- `Gate -> Portfolio` 是决策执行链
- `Portfolio -> Feedback -> Model` 是闭环校准链

## v2.0 核心变化

- Gate 不再只是单项目判断，而是投资组合约束的一部分
- Portfolio 成为一等模块
- Feedback 成为一等模块
