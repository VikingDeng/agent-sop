# SOP-run-development: 0→1 development 结果 Profile

- **层级**: tier1-skeleton
- **落实纪律**: P1(产品能力与 non-goals) P2(真实行为验收) P3(失败与替代路径语义显式) P4(关键 claim 可追溯)
- **绑定骨架**: development
- **通用性档位**: U1（开发机制通用；技术栈、命令与工具由项目注入）
- **版本**: v3

## 触发条件

- `[信号自触发]` 从 0 到 1 交付应用、服务、库、CLI、数据管线或其他可用软件成品；
- `[信号自触发]` 现有项目中新增一组跨模块的完整产品能力，需要重新推导 domain/state 语义与端到端验收。

局部、语义明确的 bug fix 默认只使用 Supervisor 和现有项目 oracle；不为了流程完整而扩展为 0→1 profile。

## 前置条件

- 能识别至少一个使用者、调用方或运营者要获得的可观察能力；
- 能从用户请求、closest project instructions、现有行为或项目事实中推出可开始首个 vertical slice 的最小结果契约；
- 已确定授权 workspace。关键产品语义必须靠猜时，只阻断依赖该决定的部分。

## 依赖 SOP

→ tier0-core/autonomous-supervisor.md（唯一通用运行时决策源）。

→ tier1-skeleton/write-contract.md（冻结与规模相称的开发结果契约）。

→ tier1-skeleton/drift-check.md（在可信漂移信号或交付边界核对范围）。

→ tier0-core/build-oracle.md（现有验收路径不能区分 claim 与具体失败时）。

→ tier0-core/no-fallback-review.md（错误、恢复或降级路径影响结果语义时）。

## 步骤

1. **冻结能力契约，不预设页面或 endpoint。** 使用 `write-contract` 明确主要 consumer、使用情境、可观察结果、non-goals、授权范围与验收证据。把核心需求表达为“actor/caller 可以完成什么”，而不是“必须有某个组件或文件”。明确 feature、issue、spec 或 public contract 已经选择的方向直接进入实现，不追加 discovery 仪式。
2. **只在产品方向真实开放时搜索；价值 claim 单独验收。** 用户要求 ideation/比较，或目标仍容许多个实质不同产品方向时，识别真实目标用户/调用方、发生情境、现有替代和一个会否定路线的关键假设；形成少量实质不同候选，并用相同的 outcome-derived 判据和可比证据判断。已有使用数据、真实工作流、用户提供的事实、支持记录、实际交互或最小行为 probe 可以支持价值判断；合成人格、Agent 偏好和漂亮 prototype 只能生成假设。明确 feature/issue/spec 的方向不因缺少价值证据而重新搜索或 pivot；这不妨碍如实完成“实现了该能力”的 claim，但不能升级为“用户需要、值得扩展或方向已验证”。
3. **推导最小 domain model 与语义边界。** 只对影响行为的概念确定 identity、关系、所有权、持久性和关键不变式；有状态资源按实际语义推导转换与恢复，不机械要求 CRUD。仅在 claim 触发时明确 public interface、兼容、数据、副作用、一致性、并发、安全、性能或运维边界。public API 有多个可信解释时，用调用方可观察行为比较默认值、显式 opt-in、错误/清理与资源状态保持；无歧义时不制造矩阵，也不为假想未来预建平台层。
4. **选择第一个判别性 vertical slice。** 它必须从真实输入/交互穿过实际产品边界到达用户可观察结果，并优先关闭会推翻价值、集成可行性或整体架构的最高信息风险。中间 mock 可用于局部开发，不能证明该 slice 已闭环。方向开放时，关键价值假设被真实证据否定、剩余学习成本超过预期价值即可 kill/pivot；方向已冻结时，可行性 no-go 只停止受影响路线并触发报告/re-contract，不能自行改题。证据仍在减少当前决策不确定性时继续，不因已有代码而扩展功能。
5. **推导最小 critical journeys 与特殊 claim Oracle。** 从冻结能力和 domain/state 语义选择能区分“可用产品”与“happy path demo”的旅程；只为具体失败路径增加 empty/missing、invalid/denied、retry/reload/restart 或 partial-failure。若声称 comparison/compare/对比，要验证用户能在同一决策上下文比较契约数量和类型的对象；单个 ranking/recommendation 不能冒充 comparison。
6. **在最短真实反馈回路中实现。** 每次先关闭一个决定性未知量，再用与当前 claim 相称的 oracle 检查。局部测试可定位错误，但共享实现假设的测试不能单独证明最终能力；真实外部集成由最便宜的实际调用或契约 oracle 支持。
7. **对 UI-complete claim 使用真实 render oracle。** 在真实渲染运行时操作适用 journeys，检查可见结果、交互、状态反馈及会否定 claim 的运行时失败。构建、类型检查、组件存在或静态截图不能单独证明交互完成；非 UI 交付不触发此 gate，具体工具与视觉标准由项目契约或 Skill/Oracle 提供。
8. **在 integration/handoff/delivery 边界收口。** 使用 `drift-check` 核对实际 diff、产品语义与交付 claim，然后运行最小充分验收。只有当前 claim 确实包含价值/方向结论时才要求相应真实价值证据；否则清楚区分“能力已交付”和“价值仍未建立”。只因具体风险升级全量测试、性能/安全/可达性检查或独立 review。

## 门禁

- `[AUTO]` 若核心 capability、重要 non-goal 或可信验收方法完全无法确定，阻断依赖该信息的实现。
- `[AUTO]` 若交付 claim 包含“真实用户需要/值得扩展/方向已验证”，但没有任何真实价值信号，相关价值 claim 保持 `NOT_ESTABLISHED`；不阻断方向已冻结的软件实现。
- `[RUNTIME]` 声称真实外部集成时需要实际集成/契约证据；声称交互 UI 完成时需要真实 render oracle 证据。环境确实阻止时可交付 `partial/ENV-BLOCKED` 与原始失败，不得宣称已验收完成。
- `[HUMAN]` 只在 Supervisor 定义的未授权语义、public/compatibility、凭据、生产/发布、不可逆状态、法律/隐私或 material/unbounded cost 边界等待决定。

固定技术栈、目录、文件名、CRUD 形状、viewport、模型、sub-agent 数量、review 轮次与 full-suite 本身都不是门禁。

## 完成判定

- 冻结的主要 capability 已从真实输入/交互贯通到用户可观察结果，而非只有局部模块或 happy path 存在；
- 对交付成立所必需的 domain identity、关系、状态转换与 critical journeys 已被实现和直接证据支持；
- comparison 或 UI-complete 等特殊 claim 符合其本身的语义与 Oracle 要求；
- 能区分能力交付与产品价值 claim；只有实际声称价值/方向成立时，才有相应真实用户、使用或行为证据；
- 关键错误和恢复语义与契约一致，没有静默成功、未授权产品扩张或把被阻断证据写成通过；
- 文档、测试、Git 和外部交付状态的报告与实际一致。

## 失败处理

保留失败命令、未通旅程和被阻 oracle 的证据；优先修复实现、缩小未知量或选择能以原 acceptance 重新验收的质量等价路径。不得为了让 demo “看起来可用”而加入未契约、未测试的 speculative runtime fallback；若 resilience/degradation 本身是用户要求的产品能力，则把它作为显式产品语义实现并验收。新路径改变 public behavior、数据/隐私边界、不可逆状态或资源承诺时进入 re-contract/HUMAN gate。

## 产物

- 存于请求、issue/plan/PR 或项目原生文档中的最小 capability contract；
- 与产品实际形态相称的 domain/state 语义和 critical journeys，不强制独立表格或指定文件；
- 可运行的产品工件与支持交付 claim 的决定性证据；
- 实际存在的局限、未验收部分和外部/Git 状态。
