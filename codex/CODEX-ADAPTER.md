# Codex 平台适配层

- **Adapter ID**: `codex-runtime`
- **版本**: v7
- **性质**: platform adapter，不是 SOP、Domain Profile 或 Skill

## 责任边界

本文档是 Codex 原生 HUMAN 交互、结果级协作沟通、Sol/Terra/Luna 路由、sub-agent 协作、WCU 计量、Codex Hooks 与 session auditor 的架构归属点。它只回答“如何在 Codex 上以可审计、成本合理的方式执行”，不回答“什么结果算成功”。

权威顺序是：用户和 closest project instructions → [`PRINCIPLES.md`](../PRINCIPLES.md) 与 [`sop/tier0-core/autonomous-supervisor.md`](../sop/tier0-core/autonomous-supervisor.md) → 已触发的 Domain Profile → 本 Adapter → 可替换 Skill/Oracle/role recipe。本 Adapter 不得：

- 降低或扩大冻结的 outcome、non-goals、acceptance 或 research claim；
- 新建 HUMAN 边界、领域 gate、必选 Skill、固定 review 轮次或产品 artifact；
- 把某个模型、role、Hook marker、package field、WCU 数字或 auditor 结果当作产品/研究验收证据；
- 以平台限制为理由静默改变成功定义。

安装、路由配置和命令的当前做法见 [`README.md`](README.md)；本文档不复制那些易变实现细节。

## HUMAN 决策的原生交互绑定

HUMAN gate 是否成立只由 Kernel 决定，本 Adapter 不新增、扩大或取消 gate。命中真实未决决定且当前会话提供 `request_user_input` 时，优先使用原生弹窗，不把普通任务变成默认问卷：

- 默认每次只发一个问题；问题是一句可直接决定方向的话，header 不超过 12 个字符；
- 提供 2–3 个互斥选项，1–5 个词的短 label 只命名用户可见选择，description 用一句话说明结果或取舍；
- 把 Kernel 选出的推荐项放在第一位，并在 label 后加 `(Recommended)`；不要手工添加 `Other`，客户端会提供自由输入；
- 选项表达 outcome、scope、acceptance 或授权边界，不让用户代替 Agent 选择库、内部架构、命令或排错步骤；
- 收到答案后回到 Kernel 重新 `RESOLVE/CONTRACT`，不预先排出固定问题链，也不把该答复视为对其他边界的概括授权。用户追问原因时解释当前分叉并保持它未决；用户明确委托 Agent 决定时，只在 Kernel 允许安全默认的范围内继续。

如果当前 Codex 版本、模式或客户端没有暴露 `request_user_input`，或一次符合当前 schema 的调用失败，通过普通对话提出表达同一决定的一句简洁自然语言问题，说明关键影响与推荐后等待；只有更高优先级的当前模式指令允许时才在文本中列出选项。工具缺失不是用户授权，也不能成为扩大问题数量、降低 acceptance、改变契约或展示内部分类的理由。若 Kernel 判定没有阻断性决定，则不调用该工具、不发澄清消息，直接调查、采用安全默认或执行。

原生交互能力按当前 turn 的实际工具暴露判断，不把安装配置、feature maturity、磁盘文件、Hook marker 或旧 turn 成功当作本次可用性的证明。对每个当前决定只跟踪最小生命周期：`configured/advertised → observed available → invoked → answered | cancelled | failed | unavailable`。只有绑定当前未决问题的有效 answer 才能解除 gate；cancel、空答、调用失败、过期问题答案或用户仅要求解释都不能推断选择。失败后只对同一决定使用上述文本 fallback，不循环 probe、不写永久 unavailable 标记，也不自动安装 Skill/plugin 作为替代；新 turn 需要时重新观察能力。

## 结果级协作沟通

Kernel 决定 outcome 事件的触发条件；本 Adapter 只把这些事件映射到 Codex 的 commentary/final channel。当前平台若要求更频繁的活性更新，将相邻技术动作合并成同一结果状态，不逐条播报命令、文件或工具调用。

每次更新尽量压缩为“当前结果状态或变化 → 为什么影响用户结果 → 下一动作”。已知上下文只引用与当前决定有关的部分，不重复要求用户确认；必要的一句话 outcome 回放不能变成新的仪式。不得在 commentary/final 暴露 Requirement Judgment 分类、完整 intent frame、推断偏好、敏感 provenance 或无关历史。最终答复仍先交付已达到的结果与决定性证据，再说明实际限制和 Git/外部状态。

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

开放式 Option Search 中，根 Agent/Sol 保留问题定义、候选是否实质不同、致命反例裁决、方向冻结与最终集成权；Terra 适合并行做只读的真实工作流调查、最近邻/跨领域碰撞、falsifier、产品/视觉 critique 与普通 Browser QA；Luna 只在问题、输入、Oracle 和停止条件已经稳定时运行廉价 probe、批量检索/测试或实现候选 slice。并行用于增加独立证据，选择与核心不变式裁决保持串行；候选生成者、Reviewer 和 worker 都不能把方向标为已批准。多个 writer 只有在独立 worktree 或明确文件边界下才可并行，核心语义未定时不让实现 swarm 用代码量替代选择。

以上是可被实证修正的偏好，不是资格表。优先选择能保持 acceptance 的最低成本路径；模型/role 不可用或证据表明错配时，可显式更换路由，但要以未改变的 acceptance 重新验收。不得把“用了 Sol”写成质量证据，也不得把“只用 Luna”当作质量失败。

当前成本诊断可用：

```text
WCU = 25 * T_sol + 10 * T_terra + 1 * T_luna
```

`T_*` 使用审计器可归因的实际 token；能捕获时纳入 cached input 与 monitoring/polling 开销。WCU 用于比较在相同 acceptance 下的路由效率，不是完成门禁。不完整归因标记 `[UNCERTAIN/PARTIAL]`，不推导为零。只有成本将越过已授权的 material/unbounded resource boundary 时，才因 Supervisor 而进入 HUMAN gate。

## Sub-agent 协作与生命周期

- 只委派能独立交付的 coherent outcome package；packet 至少给出 objective、scope/write boundary、必要输入、acceptance evidence 与 stop/escalation condition。
- child packet 只携带完成该 package 必需的契约、非敏感证据指针，以及 package 必需且非敏感的作用域内已确认偏好；不转发完整对话、无关 memory/continuity、推断偏好、secret、敏感 provenance 或可间接还原敏感内容的 evidence pointer。敏感偏好只有在用户明确授权该 child 与具体用途时才可传递；偏好不能因进入 child context 而扩大 scope 或变成授权。
- 优先根 Agent 扁平路由；不把 child 再委派 child、固定并发数或某个 role 存在当作成功条件。
- 不按单条命令拆包，不传入与结果无关的完整历史。优先仓库 artifact 和最小自包含 packet，仅在具体依赖无法压缩时继承最少必要 context。
- 核心不变式未确定且阻断 critical path 时，先由根 Agent、判别 oracle 或紧凑 architect package 关闭；不预先让多个 implementer/reviewer 在同一未知量上竞争。
- 有真实不重叠工作时才并行。下一步依赖 child 结果时使用一次与 package 相称的 bounded wait；预计需要数分钟的实现/review 不用连续 20–60 秒轮询。timeout 只表示未完成，不是负面 verdict：先做真实不重叠工作，若没有则用一个更符合剩余工作的 wait；同一 child 连续短轮询是成本 finding，不是进度策略。
- 每个 open child 必须有当前用途或近期 dependent input；实现者可在一次明确即将到来的 review/correction 期间短暂保留。结果已消费且没有具体下一输入时立即显式 close，再创建下一 child；completed 但未 close 仍占 open capacity。达到并发上限前先消费并关闭已完成 child，而不是等 thread-limit 后再清理。不再需要的 child 明确取消并记录未完成范围；平台无法确认时记为 `OPEN/UNKNOWN`，不声称已关闭。
- “独立 review”只在实际发生了具有足够独立输入或错误路径的第二视角时成立；role 名和 spawn 记录本身不证明 review 质量。

## 长程目标、handoff 与外部调度

原生持久 goal 只在用户明确要求长程/持续推进，且目标有可观察终点、可运行 verifier、后续动作不需要反复猜用户偏好、权限与成本可界定时启用。goal 保存稳定目标，不保存完整对话或把 token budget 当完成条件。目标和契约仍稳定、当前上下文有决策价值时继续同一顶层 task；目标改变、上下文已被噪声淹没或需要真正独立视角时使用新 task，并从项目事实恢复，不 fork 全历史。

只有真实跨 task/session、外部 scheduler、不可廉价重做或交接需要时，才维护一个项目原生的轻量 continuity record；不要求固定文件名。它只保存恢复当前决定所需的信息：契约/范围与 non-goals、已证实事实、已作决定及其证据/理由、workspace/commit/run/当前最佳 artifact 身份、已完成和未完成/失败证据、下一判别动作、blocker 与必须交给用户的授权分叉。若有活跃 worker，再记录可观察 lifecycle；若存在自动 retry 或外部副作用，再记录工作是 `replayable`、`resume_only` 还是 `externally_effectful` 及稳定 run/idempotency identity。没有真实恢复需要时不创建 packet、ledger、lease 或 heartbeat。

外部 scheduler 只有同时满足四项 readiness 才可接管：**contract-ready**（outcome/non-goals/authority/acceptance 已稳定）、**oracle-ready**（Agent 能由直接证据区分改善与退化）、**state-ready**（workspace/run/artifact 与恢复语义可确认）和 **decomposition-ready**（子任务不需要反复重定核心产品/研究语义）。并发、成本与外部动作包络也必须已界定。它只能接管启动、等待、取消、保留、恢复和有界 retry，不能选择产品/研究方向、改变 contract/acceptance/method、跨越 HUMAN 边界或代替项目 Oracle 给最终 verdict。任一 readiness 失效、同类失败重复且无新信息、局部补丁只增加复杂度、需要 re-contract/HUMAN 或 acceptance 已满足时停止循环。`timeout` 是 `INCOMPLETE/UNKNOWN`，不是失败或重派许可；有副作用或身份不明的工作默认保留并等待接管判断，不能自动重跑。

只有能证明活跃 agent 与同一 contract、workspace、role/model 要求和 open state 匹配时才 resume；否则使用 fresh agent + compact continuity record 和项目工件，不转发完整历史。resume、重派或更换 role/model 都不重置适用预算。终态至少如实区分 completed、failed、cancelled、preserved-incomplete 与 unknown；恢复后的 producer 输出在交给 consumer 前重新检查 schema/contract compatibility。

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
