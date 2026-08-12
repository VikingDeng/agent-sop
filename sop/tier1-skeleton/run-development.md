# SOP-run-development: 0→1 development 结果 Profile

- **层级**: tier1-skeleton
- **落实纪律**: P1(产品能力与 non-goals) P2(真实行为验收) P3(失败与替代路径语义显式) P4(关键 claim 可追溯)
- **绑定骨架**: development
- **通用性档位**: U1（开发机制通用；技术栈、命令与工具由项目注入）
- **版本**: v2

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

1. **冻结能力契约和交付等级，不预设页面或 endpoint。** 使用 `write-contract` 明确主要 consumer、使用情境、可观察结果、non-goals、授权范围与验收证据，并从用户原话区分 `bounded slice/prototype` 与 `complete product`。用户明确要求“完整、成品、production-quality、可直接体验”时，不能静默降级成 MVP、可点击原型或单一 happy path；交付等级约束结果广度，不自动增加架构、文档或流程。
2. **推导最小 domain model。** 只对影响行为的概念确定 identity、关系、所有权、持久性和关键不变式。若产品包含有状态资源，按实际语义推导可用状态、合法转换、失败转换及可恢复边界；不机械要求 CRUD、delete 或任何固定 lifecycle。
3. **绑定真实后端与集成语义。** 仅在 claim 触发时明确 public interface、兼容、输入验证、身份/所有权/授权、持久性、状态转换、一致性/并发、retry/idempotency、外部失败、安全、性能或可运维边界。不为假想未来需求预建抽象；本地单用户产品不被机械要求登录或分布式机制。但若 `complete product` 声称 server-backed、多 actor、共享状态或真实集成，请求时临时 seed 的内存数据、把多种 domain transition 塞进无类型/无验证字符串分派且没有独立语义的 endpoint、静态 mock 或无所有权的数据修改不能充当相应语义已完成的证据。
4. **为人机界面冻结产品特定的质量方向。** 当 `complete product` 包含用户界面时，在写大批 UI 代码前用现有品牌/设计系统、用户给定参考，或原生能力/一个合格 Visual Author，从真实领域材料推导最小但可观察的内容语气、信息层级、typography/视觉身份、目标 viewport 和适用状态。它可以是对话或计划中的几行，不强制新建设计文档。若界面去掉 logo 和文案后可无差别套给无关产品，或用通用 dashboard/card 模板代替领域材料与主任务，则不能支持“有产品设计/高质量成品”的 claim。Skill 只提供候选方向，不能改变功能契约或自行验收。
5. **选择第一个端到端 vertical slice。** 它必须穿过实际产品边界，从真实输入或交互到用户可观察结果，并优先关闭一个会否定整体架构的高信息风险。中间 mock 可用于局部开发，但不能充当该 slice 已闭环的证据；模拟的核心数据或服务必须显式标注，不能被报告为真实集成。
6. **推导 critical journeys。** 从冻结能力、交付等级和 domain/state 语义中选择能区分“可用产品”与“只有 happy path demo”的最小旅程集。每条适用旅程表达初始状态、用户/调用方动作、预期转换与可观察结果；只在存在具体失败路径时加入 empty/missing、invalid/denied、retry/reload/restart 或 partial-failure 情形。
7. **保真特殊产品语义。** 若契约声称 comparison/compare/对比，要验证用户能选择契约数量与类型的多个对象，并在同一决策上下文看到声称的关键指标或差异。单个 ranking/recommendation 不能冒充 comparison；未声称 comparison 的产品不触发此要求。
8. **在最短真实反馈回路中实现。** 每次先关闭一个决定性未知量，然后用与当前 claim 相称的 oracle 检查。局部测试可快速定位错误，但共享同一实现假设的测试不能单独证明最终能力。外部 API、协议或平台集成的真实性由最便宜的实际调用或契约 oracle 支持。
9. **对 UI-complete claim 使用真实 render oracle。** 在真实渲染运行时中操作适用 critical journeys，检查可见结果、交互、状态反馈、目标 viewport 及会否定 claim 的 console/request/runtime 失败。构建、类型检查、组件存在或代码审查不能单独证明 UI 完成；静态截图只支持它实际展示的视觉 claim。若 `complete product` 同时声称 product-grade 视觉质量，最终交付前还要由未主导该视觉实现的观察者基于冻结方向和同状态真实截图做一次结果审查，并只修复会否定 claim 的具体问题；这不是所有 UI 的固定 review 或循环门禁。非 UI 交付不触发 browser/render gate。
10. **在 integration/handoff/delivery 边界收口。** 使用 `drift-check` 核对实际 diff、交付等级和产品语义，然后运行能支持最终 claim 的最小验收集。只因具体风险升级全量测试、性能/安全/可达性检查或额外 review，不把它们变成所有项目的仪式。

## 门禁

- `[AUTO]` 若核心 capability、重要 non-goal 或可信验收方法完全无法确定，阻断依赖该信息的实现。
- `[RUNTIME]` 声称真实外部集成时需要实际集成/契约证据；声称交互 UI 完成时需要真实 render oracle 证据。环境确实阻止时可交付 `partial/ENV-BLOCKED` 与原始失败，不得宣称已验收完成。
- `[HUMAN]` 只在 Supervisor 定义的未授权语义、public/compatibility、凭据、生产/发布、不可逆状态、法律/隐私或 material/unbounded cost 边界等待决定。

固定技术栈、目录、文件名、CRUD 形状、viewport、模型、sub-agent 数量、review 轮次与 full-suite 本身都不是门禁。

## 完成判定

- 冻结的主要 capability 已从真实输入/交互贯通到用户可观察结果，而非只有局部模块或 happy path 存在；
- 实际交付没有低于冻结的交付等级；`complete product` 的核心旅程跨越其声称的真实前端、后端、持久状态或外部集成边界，任何 mock/synthetic 部分均被显式披露；
- 对交付成立所必需的 domain identity、关系、状态转换与 critical journeys 已被实现和直接证据支持；
- comparison、server-backed、UI-complete 或 product-grade visual quality 等特殊 claim 符合其本身的语义与 Oracle 要求；
- 关键错误和恢复语义与契约一致，没有静默成功、未授权产品扩张或把被阻断证据写成通过；
- 文档、测试、Git 和外部交付状态的报告与实际一致。

## 失败处理

保留失败命令、未通旅程和被阻 oracle 的证据；优先修复实现、缩小未知量或选择能以原 acceptance 重新验收的质量等价路径。不得为了让 demo “看起来可用”而加入未契约、未测试的 speculative runtime fallback；若 resilience/degradation 本身是用户要求的产品能力，则把它作为显式产品语义实现并验收。新路径改变 public behavior、数据/隐私边界、不可逆状态或资源承诺时进入 re-contract/HUMAN gate。

## 产物

- 存于请求、issue/plan/PR 或项目原生文档中的最小 capability contract；
- 与产品实际形态相称的 domain/state 语义和 critical journeys，不强制独立表格或指定文件；
- 可运行的产品工件与支持交付 claim 的决定性证据；
- 实际存在的局限、未验收部分和外部/Git 状态。
