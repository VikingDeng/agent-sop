# Codex 平台适配层

- **Adapter ID**: `codex-runtime`
- **版本**: v3
- **性质**: platform adapter，不是 SOP、Domain Profile 或 Skill

## 责任边界

本文档是 Sol/Terra/Luna 路由、sub-agent 协作、WCU 计量、Codex Hooks 与 session auditor 的架构归属点。它只回答“如何在 Codex 上以可审计、成本合理的方式执行”，不回答“什么结果算成功”。

权威顺序是：用户和 closest project instructions → [`PRINCIPLES.md`](../PRINCIPLES.md) 与 [`sop/tier0-core/autonomous-supervisor.md`](../sop/tier0-core/autonomous-supervisor.md) → 已触发的 Domain Profile → 本 Adapter → 可替换 Skill/Oracle/role recipe。本 Adapter 不得：

- 降低或扩大冻结的 outcome、non-goals、acceptance 或 research claim；
- 新建 HUMAN 边界、领域 gate、必选 Skill、固定 review 轮次或产品 artifact；
- 把某个模型、role、Hook marker、package field、WCU 数字或 auditor 结果当作产品/研究验收证据；
- 以平台限制为理由静默改变成功定义。

安装、路由配置和命令的当前做法见 [`README.md`](README.md)；本文档不复制那些易变实现细节。

## 会话来源与运行时 provenance

一次任务的路由和过程审计只有在能确定“会话实际加载了什么”时才可信。在 Codex 能力允许时，SessionStart 应在可审计 trace 中一次性写入不可由事后 CLI 参数重解释的 source envelope：

```yaml
adapter_id: codex-runtime
adapter_version: <version>
runtime_generation: <content-addressed generation or UNKNOWN>
kernel_ref: <id/version/content identity or UNKNOWN>
domain_profile_refs: [<actually loaded profiles>]
routing_profile: advisory | strict | UNKNOWN
foreground_model: <actual family/model or UNKNOWN>
foreground_effort: <actual effort or UNKNOWN>
hook_identity: <version/content identity or UNAVAILABLE>
auditor_identity: <version/content identity or UNAVAILABLE>
session_id: <platform session identity>
started_at: <timestamp>
```

- `routing_profile` 是 Hook 在启动时报告的事实，不得由事后 `--strict` 或报告措辞改写；审计策略与该历史字段必须并列展示。
- JSONL 中的 marker 不是密码学证明，任意任务文本也可能包含同形字符串。审计器只把它标为 unverified trace observation，不允许 marker 降低调用者选择的审计严格度；缺失或冲突字段标记 `UNKNOWN/UNAVAILABLE`，不伪造版本、profile 或模型。
- provenance 缺失会降低对“使用了某路由策略/某模型/某成本”的置信度，但不单独否定由独立项目证据已证明的产品结果。若唯一验收证据本身仅存在于不完整 trace，则该 claim 仍缺证据。

## 模型与 WCU 路由

路由是受 outcome contract 约束的成本优化，不是模型等级仪式：

- **Luna** 优先承担边界稳定、劳动密集、有直接 oracle 的实现、测试、数据处理与日志工作。
- **Terra** 优先承担跨模块语义实现、未知根因诊断、普通独立 review，以及开发/竞赛/approved-proposal 工程执行的常用顶层调度。
- **Sol** 优先承担未闭合的核心不变式、架构/研究设计、高歧义或具体高风险判断；一个紧凑 specialist 问题优于多个同质 agent 反复搜索。

选择 Sol 作为顶层不改变分工：Sol 可以调查决定性证据、作出架构/研究判断、集成少量窄改动并裁决验收，但重复写代码、跑完整测试、操作浏览器、打包或整理日志应在可用时合并成一个有直接 Oracle 的 Luna/Terra 结果包。若顶层连续承担这些机械动作，应重新切包；只有委派开销明显高于窄工作本身或没有可用角色时才留在顶层，并如实记录成本原因。

以上是可被实证修正的偏好，不是资格表。优先选择能保持 acceptance 的最低成本路径；模型/role 不可用或证据表明错配时，可显式更换路由，但要以未改变的 acceptance 重新验收。不得把“用了 Sol”写成质量证据，也不得把“只用 Luna”当作质量失败。

当前成本诊断可用：

```text
WCU = 25 * T_sol + 10 * T_terra + 1 * T_luna
```

`T_*` 使用审计器可归因的实际 token；能捕获时纳入 cached input 与 monitoring/polling 开销。WCU 用于比较在相同 acceptance 下的路由效率，不是完成门禁。不完整归因标记 `[UNCERTAIN/PARTIAL]`，不推导为零。只有成本将越过已授权的 material/unbounded resource boundary 时，才因 Supervisor 而进入 HUMAN gate。

## Sub-agent 协作与生命周期

- 只委派能独立交付的 coherent outcome package；packet 至少给出 objective、scope/write boundary、必要输入、acceptance evidence 与 stop/escalation condition。
- 优先根 Agent 扁平路由；不把 child 再委派 child、固定并发数或某个 role 存在当作成功条件。
- 不按单条命令拆包，不传入与结果无关的完整历史。优先仓库 artifact 和最小自包含 packet，仅在具体依赖无法压缩时继承最少必要 context。
- 核心不变式未确定且阻断 critical path 时，先由根 Agent、判别 oracle 或紧凑 architect package 关闭；不预先让多个 implementer/reviewer 在同一未知量上竞争。
- 有真实不重叠工作时才并行。下一步依赖 child 结果时使用一次与 package 相称的 bounded wait；预计需要数分钟的实现/review 不用连续 20–60 秒轮询。timeout 只表示未完成，不是负面 verdict：先做真实不重叠工作，若没有则用一个更符合剩余工作的 wait；同一 child 连续短轮询是成本 finding，不是进度策略。
- 每个 open child 必须有当前用途或近期 dependent input；实现者可在一次明确即将到来的 review/correction 期间短暂保留。结果已消费且没有具体下一输入时立即显式 close，再创建下一 child；completed 但未 close 仍占 open capacity。达到并发上限前先消费并关闭已完成 child，而不是等 thread-limit 后再清理。不再需要的 child 明确取消并记录未完成范围；平台无法确认时记为 `OPEN/UNKNOWN`，不声称已关闭。
- “独立 review”只在实际发生了具有足够独立输入或错误路径的第二视角时成立；role 名和 spawn 记录本身不证明 review 质量。

## Hooks 的边界

Hook 是平台协作辅助，不是安全边界、Domain Oracle 或运行时唯一事实源。

- **advisory** 是常规 profile：SessionStart 只注入精简 adapter/provenance 信息；Pre/PostToolUse 只观察明确的路由与生命周期调用，Stop 不运行 router，不因缺少 marker 或报告字段改变任务 verdict。
- **strict** 只在用户/项目显式选择的平台流程实验或高保证协作场景中启用。它可对平台工具调用或可审计性要求 fail closed，但仍不得改写产品/research acceptance。被 Hook 拒绝是执行状态，不是产品失败证据。
- Specialized tool path 可能绕过 Hook，App 对 Hook 的信任也可能需要人工确认；因此不声称 Hook 提供全面 enforcement。
- Hook 不可用大量通用语句解析、固定状态机或重复 SOP 文本来弥补平台缺少的语义证据。当 guardrail 开销接近任务价值时，简化或停用该 guardrail。

## Auditor 的边界

Session auditor 回放已发生的 trace，用于验证 actual model、token/WCU 归因、child 生命周期、工具调用和路由诚实性。它不能从缺失日志中重建事实，也不能用正则命中了某个最终报告词语来证明产品或科研成功。

- 默认审计为 process-advisory；它应分开报告 `outcome evidence`、`process observations` 与 `cost/provenance confidence`。
- CLI 默认按 advisory 规则回放；`--strict` 选择更严格的审计 policy，但不把历史 `recorded_routing_profile` 改写为 strict。两者不一致时并列报告；不可信 marker 也不能把已选择的 strict policy 降为 advisory。
- App v2 child rollout 可能在自己的 `task_started` 之前携带父线程继承历史和累计 token snapshots；审计器必须以当前 task boundary 去重，只归因该 child 的新增 usage。当前任务在首个 `turn_context` 前已经产生的 token，可以在该任务只有一个可确认模型时回填给该模型；仍有多个可能模型时保持 `unknown`。若 `task_started` 前没有合法累计基线，首个 task 内累计 snapshot 无法拆分父/child usage：从该点开始测量后续 delta，并把总量标为 `[UNCERTAIN/PARTIAL]`，不能把完整首个 snapshot 计给 child。
- 损坏、截断、缺失 descendant 或无法归因的 trace 使相应路由/成本 claim 变为 `[UNCERTAIN/PARTIAL]`；不把未知值当作零。最终报告中的明确模型/路由断言必须与 root/child trace 一致；prompt 要求、role 名与 agent 自述不能覆盖实际 `turn_context`。
- 产品结果由项目 Oracle 决定。只有当审计发现伪造证据、丢失唯一决定性证据、越权或静默改变 acceptance 时，过程 finding 才直接否定对应 outcome claim。

## 执行失败与交付

模型、Hook、auditor 或指定 role 不可用时，在授权范围内选择能保持 acceptance 的最便宜可行路径并记录替代；无法保持时诚实停止受影响部分。平台遥测缺失可以使效率或路由结论未确定，但不要要求 Agent 重复项目工作来补造流程日志。

交付优先报告实际 outcome 和决定性项目证据。只在实际发生或影响交接时补充：所用模型/路由、真实独立 review、可归因 WCU 或 `[UNCERTAIN]`、未关闭 child、Hook/auditor 局限和平台 blocker。这些 telemetry 是过程事实，不是用户产品契约的替代品。
