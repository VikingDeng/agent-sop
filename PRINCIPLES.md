# 核心纪律（Principles）

> 本仓库 SOP 的共同内核。原则约束产出质量与真实边界，不规定 Agent 的唯一行动路径。

## P1 结果契约（outcome contract）

开始前明确用户要的可观察结果、关键 non-goals、允许范围与验收证据。契约的详细程度与失败代价成比例；小而清晰的任务可以只用几句话，不要求正式 artifact。

Agent 可以改变探索顺序、实现策略和中间计划。只有当变化会改变产品语义、research claim、公开兼容承诺或资源边界时，才需要重新确认契约。

## P2 可信验收（evidence-matched verification）

用能支持实际 claim 的证据判定质量。优先真实测试、复现、性质检查、统计验证或独立对照；当第二视角能发现可信失败模式时使用独立 review。

独立性是提高置信度的手段，不是每个任务的固定仪式。简单可逆改动可以使用最小真实检查；高风险或弱 oracle 需要更强证据。

Review 必须对齐冻结契约与具体失败路径，不能用品味性要求扩大 acceptance。若发现新的可信失败路径，可触发一次合并修复或架构重置，但不得无限追加后继门禁。

## P3 失败诚实（fail honestly, adapt explicitly）

绝不伪造、吞掉或把失败写成成功。允许重试、换工具、换模型、换实现路径等显式、质量等价的 fallback，但必须用未改变的验收标准重新验证并披露触发原因。若替代路径改变 public behavior、research claim、隐私/数据边界、不可逆状态或 material/unbounded cost，必须进入 HUMAN gate 或 re-contract。

禁止的是静默降级和改变成功定义，不是所有 fallback。工具或模型不可用是执行信息，不自动等于项目失败或科研 no-go。

## P4 比例化追溯（proportional traceability）

保留足以复核关键 claim、风险决定和交付状态的来源与证据。高风险动作需要完整记录；普通工作只需关键命令、结果和改动定位，不制造无助于验收的流程台账。

## 复杂度纪律（complexity discipline）

没有具体且合理的失败路径，就不引入机制；优先平台/原生 primitive，先用最便宜能区分成败的 oracle。guardrail 成本应与潜在伤害成比例；当 guardrail 本身接近工作量时，复杂度就是待处理 finding。每个持久门禁都应有适用条件与移除条件。这些是决策规则，不是额外 artifact 或固定 checklist。

## 收纳判据

一条 SOP 应至少强化上述一项纪律，并说明其约束的是结果、证据还是风险边界。若规则只规定角色名、文件名、阶段数、review 次数或工具顺序，却不能提高验收质量，应删除或降级为可选 recipe。
