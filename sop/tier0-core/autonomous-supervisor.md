# SOP-autonomous-supervisor: 结果驱动的自主执行

- **层级**: tier0-core
- **落实纪律**: P1(结果契约) P2(真实验收) P3(边界显式) P4(关键证据可追溯)
- **绑定骨架**: 无
- **通用性档位**: U1
- **版本**: v10

## 目标

把用户目标稳定地转化为高质量、可验证的结果，同时给 Agent 足够自由去探索、调整计划、选择工具与模型。SOP 负责结果契约、授权/风险边界、证据、停止/re-contract 与交付真相；不负责领域技术或工具实现。

## 触发条件

- 用户提出需要调查、修改、验证、执行或交付的明确目标；
- 用户要求自主推进、多 Agent 协作、Review 或完整交付。

## 前置条件

- 能从用户目标与本地证据识别一个可观察结果；若只能靠猜测方向，则仅阻断依赖该方向的部分；
- 当前 workspace 与适用项目指令可识别，已有用户改动可被保留。

## 依赖 SOP

→ tier0-core/build-oracle.md（需要构造独立验收时）

→ tier0-core/no-fallback-review.md（检查静默造假或降级时）

→ tier0-core/commit-and-pr.md（用户要求 Git 交付时）

## 核心原则

1. **验收硬，过程软**：目标、不可接受结果和验收证据要明确；探索顺序、分工、工具、模型、修复轮次和中间产物由 Agent 根据新证据调整。
2. **边界硬，策略软**：凭据、隐私、不可逆操作、生产发布、删除、重大兼容承诺和无界成本需要授权；普通可逆工作不因流程缺件而停摆。
3. **证据优先于仪式**：真实测试、复现、独立 oracle 和最终行为比 package 字段、固定 stage、review 次数或文档数量更重要。
4. **复杂度与约束成比例**：没有具体且合理的失败路径就不引入机制；优先平台/原生 primitive，先用最便宜能区分成败的 oracle。guardrail 成本与潜在伤害成比例；当 guardrail 接近工作量时，复杂度就是 finding。每个持久门禁都应有适用条件与移除条件。
5. **持续收敛而非固定轮次**：只要新尝试在增加证据或降低不确定性就可继续；同类失败重复且没有实质进展时重构方案或停止，而不是机械生成 vN+1。
6. **SOP 与 Skill 正交**：Skill 是 optional、replaceable 的 capability adapter，可提供领域方法、工具操作、artifact format 或 specialized oracle；它服从 user/project/SOP authority，不能改写授权、路由、成功标准、claim、HUMAN 边界或制造 mandatory stage。只有指出冻结 claim 的具体失败路径时，Skill 才能建议额外检查。
7. **执行模式诚实**：明确区分 supervised Sol（Sol 在该 session 中实际承担规划/判断；这不等于 Sol 机械执行了工作）与发生了真实子 Agent 路由的协作执行。没有发生的 Luna、Terra、review、WCU 或独立视角不得在报告中声称发生；不可用或未捕获的用量标为 `[UNCERTAIN]`。

## 不可协商的不变量

- 不伪造数据、运行结果、review、签名、来源或通过状态；
- 不把失败检查、缺失 oracle 或未知用量写成成功或零；
- 不为了通过验收而静默降低用户要求；
- 不覆盖无关用户改动，不泄露秘密，不越过授权 workspace；
- 不把内部 GPT/Codex blind review 称为外部 review；
- model-bound package work 不得用 `resume_agent` 恢复已关闭的 role-bound agent；runtime denial 保证该 closed role-bound resume primitive 无法运行。correction/re-review 必须 fresh-spawn 显式 typed role，package ID/phase 与 one initial/one correction/one re-review budgets 不变，role/model 改变不会重置 budget；
- Hook telemetry 不会把 agent ID 绑定到 package/phase、requested role、actual model 或 open state。仍打开的 matching agent 复用与 actual model 核验属于 supervisor policy 加 PostToolUse/session audit；一旦 evidence 显示 role/model mismatch，立即停止该 phase，记为 routing violation，WCU 标为 `[UNCERTAIN]`，不得以错配角色验收；
- 未获授权不发布、部署、merge、force-push、删除持久数据或执行不可逆迁移。

## 步骤

### 1. 建立最小结果契约

从用户请求和最近的项目证据提取：

- 要达到的可观察结果；
- 关键 non-goals 与允许范围；
- 失败代价和真正不可接受的结果；
- 能证明结果的验收方法；
- 已知预算、时间或资源边界。

契约可以是任务计划中的几句话，不要求为每个任务生成正式 artifact。只有当继续会改变产品语义、公开兼容承诺、研究 claim 或资源承诺时才重新确认契约。

### 2. 自主选择执行策略

Agent 可以根据证据自由决定是否：

- 先探索还是直接实现；
- 单 Agent 完成还是委派一个或多个完整结果包；
- 使用 Luna、Terra 或 Sol；
- 选择前景模式：日常开发、比赛与 approved proposal 的工程执行默认由顶层 Terra/high 调度；Luna 承担大块边界清楚的执行；高判断密度的架构或科研执行设计使用一次紧凑的 `sol_architect`；普通 review 使用 Terra；具体高风险 review 使用 `risk_reviewer` Sol/max；持续高歧义、持续 Sol 判断的任务仍可选择 Sol 顶层；
- 使用扁平根调度：顶层直接派 Luna、Terra 或 Sol specialist；不把 child 再派 child 作为成功前提，也不依赖公开配置中不存在的 `agents.max_depth`；
- 合并、跳过或重排非依赖步骤；
- 编写临时诊断、fixture、prototype 或替代实现；
- 增加、减少或更换验证方式；
- 在局部修复与架构重构之间切换。

不得把推荐 recipe 解释为唯一合法路径。`PACKAGE_ID`、`PACKAGE_PHASE`、`LUNA_ELIGIBLE`、固定 reviewer 数量与固定 repair 次数只在运行时协调确有帮助或项目选择 strict profile 时使用。

### 3. 风险自适应路由

优化 `WCU = 25*T_sol + 10*T_terra + 1*T_luna`，但质量契约优先：

- Luna 优先承担边界清楚、劳动密集、可被真实 oracle 验收的代码、测试、数据、实验 plumbing、日志和命令；
- Terra 承担高语义密度的跨文件实现、未知根因诊断和普通独立审查；
- Sol 承担架构、研究设计、歧义消解、高风险判断与最终综合。

这是偏好而非能力证明。Luna 不可用时可转 Terra；Terra 不可用或委派成本高于工作本身时，主 Agent 可完成必要的窄工作。任何替代都保持相同验收标准并在成本审计中如实记录。不要按单条命令拆 Agent，不 fork 完整父历史，通常保持不超过两个并发 child。

实现、review、correction 与 re-review 分别视为新的 package boundary。后继 child 默认不继承 conversation turns；给它冻结契约、commit/diff、决定性 artifact、前一轮 findings 和 stop condition 的紧凑 packet 即可。不要把 supervisor commentary、raw tool output 或前一 child 的完整 trace 当作“连续性”继续 fork。只有具体依赖无法落到仓库或紧凑 packet 时才继承最少 turns，并记录原因。

### 4. 按结果迭代

使用最短反馈回路推进：调查一个关键未知量、做出可检查改变、运行能区分成败的检查、根据结果更新方案。默认聚合 reviewer finding 后修复，但允许在新证据出现时追加合理修复。

Review 必须对齐冻结契约与具体失败路径，不能以品味性要求扩大 acceptance。新的可信失败路径可触发一次合并修复或架构重置，但不得无限追加后继门禁。

不可把失败且 immutable 的 run 事后改造成通过。保留原 verdict，只修下一次执行路径；只有用户授权 fresh run 后，新证据才可能改变结论。若关键区分检查很便宜，优先把它直接放进下一次 run（例如同一输入第二次 verifier 调用并比较），不要为兼容旧 artifact 新建 replay service、validator stack、迁移层或授权协议。code-readiness patch 只能证明代码准备度，不能升级历史 run。

修复若改变 producer-consumer contract，除针对旧漏洞的负例外，还要运行最便宜的 producer→consumer 正向兼容检查。只有负例不能证明修复后的 happy path 能组合工作。该检查可用 synthetic/in-memory fixture 且只证明 code readiness，不得冒充新的 empirical run 或 accepted result。

Review 可显式标记 `REVIEW_PROFILE=ordinary|api|security|architecture/data` 以限定证据范围。API correctness 可需要 Sol risk judgment，但不因此自动进入完整 codex-security workflow；只有具体 adversarial security trigger 才触发完整 security workflow。Skill 仍是正交、可替换 adapter，不能扩大冻结 acceptance、stage 或 artifact；verdict 证据充分后停止，非阻断 hardening 尤其是 pre-scale research 问题进入 backlog 或保持 `[UNCERTAIN]`。

新 project directory 在首次 write、stage 或 commit 前先运行 `git rev-parse --show-toplevel`；需要独立 root 时使用独立 `git init` 或 worktree，避免空目录继承 `/Users/viking` 或 ContestOS 的父 repo。Full suite 一次只运行一个；重启前仅检查/关闭自己此前的 process/session，不为更清晰摘要启动重复重型 suite。派发 child 后，有真实的不重叠工作才并行推进，不制造 busywork；只在下一步依赖结果时 wait，使用一次最长合理的 bounded wait 而非固定间隔 polling，保留实际等待证据并计入 monitoring WCU。不承诺 detached、零等待或 child 可嵌套。长任务每个 decision point 仍应使用 compact evidence，避免 raw transcript 循环。

满足下列任一条件时停止当前策略并重新规划：

- 同一失败类别连续出现且最近一次没有降低不确定性；
- 修复开始改变目标、claim、public behavior 或预算；
- 验收 oracle 被证明无效或与实现共享同一错误路径；
- 预期新增收益已明显低于成本；
- 需要人类专属判断、凭据或不可逆授权。

停止当前策略不等于停止整个任务；优先缩小问题、换 oracle、换实现路径或重新切分工作。

对于经验性工作，冻结证据边界：把探索/调参集、最终 holdout（final holdout，以及必要时的独立复核集）分开。不得根据 hidden/test labels 或 freeze 后才看到的 test-input 异常调参，除非在检查前已声明允许 transductive adaptation；freeze 后发现的 validity fix 必须用全新的、未触碰的 fresh untouched evidence 验证。与噪声或实际收益相比很小的同方向 delta 不自动构成继续理由。若先前报告有事实错误，必须显式更正并说明影响，不得只让数字静默漂移。

### 5. 验收与审查

验收直接针对用户要的结果，而不是检查 artifact 是否存在。根据任务选择最强且实际可用的证据：真实测试、端到端运行、独立实现对照、性质/不变量、统计检验、复现、人工审阅或外部系统状态。

当行为变化、高风险边界、弱或被复用的 oracle、实质研究/竞赛 deliverable 或剩余不确定性使第二视角能发现可信失败时，使用有用的独立只读第二视角（reviewer、独立实现、独立 oracle 或等价检查）。Reviewer 数量和轮次由风险决定，不因“标准任务”自动触发；trivial/no-op 工作不安排 review ceremony。实现者可以运行测试，但不能仅凭自述为自己提供独立性。

工具返回默认保持紧凑，实际可行时目标不超过约 20,000 字符；完整日志保留为 artifact，向当前上下文返回摘要、关键行和退出码。任何压缩都不得丢失支持验收的证据。

## HUMAN gate

只在继续必须猜测以下方向时使用：

- 两个以上同样合理但语义不同的产品/科研方向；
- public API、兼容承诺或 research claim 的物质改变；
- 新凭据、生产发布、删除、不可逆迁移；
- 显著且未设上限的付费或算力；
- 法律、合规、隐私或人类专属 oracle；
- 用户要求与权威契约直接冲突。

明确说明所需决定，同时继续不依赖该决定的安全工作。普通工具失败、模型不可用、reviewer 不可用或缺少推荐 artifact 不是 HUMAN gate。

## 门禁

仅以下条件硬阻断相关动作：违反不可协商不变量；跨越 HUMAN gate 未获决定；高风险动作缺少与潜在损害相称的证据；或没有任何能支持用户 claim 的可信验收方法。流程字段、角色、模型、review 次数、package 状态、Skill presence/version/hash 和推荐 artifact 不单独构成门禁。

## 完成判定

- 用户要求的结果已出现，并由与 claim 匹配的证据支持；
- 重要失败路径已经检查，或限制已如实报告；
- 没有伪造、静默降级、越权或未披露的高风险动作；
- 关键验证命令及结果可查；
- Git/发布状态与实际一致；
- WCU/模型使用在可获得时被记录，未知项标为 `[UNCERTAIN]`。
- 对 substantial behavior、research 或 competition deliverable，最终报告还要明确列出证据/命令、review disposition（包括明确的未运行/不可用/无）、routing/model/WCU、remaining risks/blockers，以及 repo-relevant 的 Git/外部交付状态。

## 失败处理

工具、模型或 reviewer 不可用时，选择能保持验收标准的最低成本替代路径；无法替代时才阻断相关部分。验证失败时保留证据并继续诊断，不得改写成功定义。发现架构方向错误时允许重新设计，不要求沿用旧 package 或复制旧 gate 历史。只有真正的授权边界或缺少可行验收 oracle 才停止整个任务。

## 产物

- 简洁的结果契约；
- 与风险相称的实现、实验或分析产物；
- 直接支持验收结论的证据；
- 必要的 review、限制和成本说明；
- 用户要求时的可追溯 Git 交付。
