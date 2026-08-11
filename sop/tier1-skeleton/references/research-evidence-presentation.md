# Research evidence presentation contract

本 reference 供 `research-execution-grill.md` 与 `run-experiment.md` 使用。它规范科研结果如何从真实 run 派生并展示，不规定项目必须创建固定文件名、数据库或额外 dashboard。项目可把这些视图写入现有 report、实验追踪系统或 Markdown；字段只在与当前 claim 相关时启用。

## 1. 证据分层

每个 run 在启动前声明一种 evidence class，并记录 `paper_eligible`：

| Evidence class | 允许用途 | `paper_eligible` 默认值 | 禁止用途 |
|---|---|---:|---|
| `diagnostic` | wiring、schema、异常路径、资源估计、输出格式 | `false` | claim、GO、调参结论、最终表 |
| `code_readiness` | deterministic fixture、producer→consumer、naive/reference 对拍 | `false` | 经验性 claim、历史 run 追认、最终表 |
| `exploratory` | 真实任务/数据上的预声明 pilot、failure-mode 判断、GO/NO-GO | `false`，除非项目协议明确允许作为探索性论文证据 | confirmatory claim、事后改 protocol |
| `confirmatory` | 冻结 protocol 后的正式 claim 验证 | 仅全部 eligibility 条件满足时为 `true` | 用未披露变更、fallback 或失效 oracle 产出结论 |

`paper_eligible=true` 至少要求：真实任务与数据；冻结的 claim、primary estimand、baseline、split、分析方法和预算；方法 fidelity/code readiness 已有匹配证据；本 run 无 mock/stub/synthetic input、自动 runtime fallback、未披露缓存或 dirty code；oracle 有效；原始产物可追溯。一个字段为 `true` 不是自证，checker/report 必须能从 run evidence 复核这些条件。

## 2. 中间实验视图

项目维护一个从 immutable run records 生成的紧凑 run view。不得只展示成功或最高分 run。最小列为：

| Run | Class | Paper eligible | 本轮唯一问题/改变量 | 数据与 split | Seed/N | Status | Primary estimate | Oracle | 失败/排除原因 | Compute | Decision |
|---|---|---:|---|---|---|---|---|---|---|---|---|

规则：

- `crashed`、`invalid`、`timeout`、`killed`、`not_run` 与科学上的负结果分开表示；不得填 0 或从表中消失。
- 同一 run 改多个关键变量时必须披露，不能把结果归因给其中一个变量。
- smoke、synthetic fixture、mock/stub/fallback 结果留在中间视图，但始终 `paper_eligible=false`，不能进入 claim summary。
- 修复后的新 run 使用新 run ID；旧 verdict 原样保留，不覆盖、不回填。
- 中间视图链接或标注 raw result、配置、日志、代码版本和 checker/oracle 结论；不要求把大日志复制进报告。

## 3. 数据与预处理视图

当数据处理可能影响 claim 时，展示来源到最终分析集的数量与排除路径：

| Stage | Input N | Kept N | Removed/invalid N | 规则或原因 | Missing/contamination | 来源/版本或 fingerprint |
|---|---:|---:|---:|---|---|---|

- 预处理、过滤、去重、解析失败、人工排除与缺失值策略必须区分；不得只给最终 N。
- train/validation/holdout 的单位、时间边界和重叠检查应可见；无法检查污染时明确写 `cannot_rule_out`。
- 数据变化产生新身份并触发新 run；不得让现有 run 的数据含义静默漂移。
- 只有 claim 不依赖数据流时才可把本视图记为 `not_applicable`。

## 4. 最终结果表

每个 primary claim 至少有一个 authoritative table 或等价结构化视图，由冻结 protocol 下的 run records 自动生成；指标与 effect estimate 只消费 eligible runs，invalid/timeout 等正式尝试只贡献状态与计数。推荐最小列为：

| Method | Backbone/Version | Benchmark/Split | Eval/Tuning budget | N/Seeds | Primary metric | Estimate + uncertainty | Predeclared contrast/effect + uncertainty | Invalid/timeout | Compute/cost | Run IDs | Claim verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|

展示约束：

1. 行顺序和 primary metric 来自冻结 protocol，不按看到结果后的故事重排；关键 baseline、主方法与 claim 所需 ablation 使用可比较设置。
2. 不同 backbone、prompt/template、backend、数据版本、评测预算或 tuning budget 不可混成公平对比；必要时分 panel，并在差异列或脚注说明。
3. 多次观测展示 point estimate、匹配的不确定性和有效 N；比较性 claim 还要展示预声明 contrast/effect、比较单位与匹配不确定性。只报 best seed、只画均值或用标准差替代适用的置信区间都不合格。
4. `invalid`、`timeout` 和任务失败数进入表或紧邻表的完整注释；不得从分母静默剔除。
5. 小数精度、单位、`↑/↓` 和加粗规则在表内一致。加粗只表示预声明规则下的视觉突出，不代替统计结论。
6. 数值来自 raw results 的确定性聚合；允许人工调整排版和文字，但禁止手填、复制论文旧数、截图读数或在生成后手改结果值。
7. `diagnostic`、`code_readiness` 与默认不 eligible 的 exploratory run 不进入 authoritative final table。冻结 protocol 下 invalid/timeout 的 confirmatory attempt 可显示为无 estimate 的状态/计数，但绝不能参与指标聚合；若论文披露探索性结果，必须单独标注其 class 和限制。
8. `Claim verdict` 保留原 contract 的状态，例如 `SUPPORTED`、`FALSIFIED`、`NOT_ESTABLISHED`、`BLOCKED`；次级弱发现不得替换原 claim 的 verdict。

## 5. 图与曲线

- 图从与表相同的结构化数据生成；表与图数值不一致即失败。
- 有重复观测时优先同时展示 raw points/distribution 与 aggregate uncertainty；不能只画一条平滑均值线。
- smoothing、截断、归一化、对数轴和样本排除必须在 caption 或图例声明；原始未平滑数据保持可查。
- 训练/RL 曲线标出 seed/replicate 数、实际 step/token/episode 横轴、失败或提前停止 run；不得只展示最好 seed。
- efficiency 图的质量指标和成本指标来自同一 run，或明确标注不可直接联合解释。

## 6. 权威来源与交付

- raw run record 是事实来源；中间视图和最终表是派生视图，不反向修改 raw evidence。
- 报告必须能从 headline number 回到组成它的 run IDs、配置和聚合代码。
- 生成 final table 的命令或入口需要记录；无需为普通项目引入新的 ledger、服务或签名系统。
- 若无法可靠生成某项展示，标注缺失与影响，不用占位表、合成数字或手工估计补齐。
