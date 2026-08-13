# SOP-run-development: 0→1 development 结果 Profile

- **层级**: tier1-skeleton
- **落实纪律**: P1(产品能力与 non-goals) P2(真实行为验收) P3(失败与替代路径语义显式) P4(关键 claim 可追溯)
- **绑定骨架**: development
- **通用性档位**: U1（开发机制通用；技术栈、命令与工具由项目注入）
- **版本**: v4

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

→ tier2-activity/option-search.md（产品方向确实未冻结且选错方向代价较高时）。

## 步骤

1. **冻结能力契约与交付等级，不预设页面或 endpoint。** 使用 `write-contract` 明确主要 consumer、使用情境、可观察结果、non-goals、授权范围与验收证据，并从用户原话区分局部 slice/prototype 与完整成品。用户明确要求“完整、高质量、production-quality、可直接体验”时，不能静默降级成 MVP、静态 mock、单一 happy path 或“文件齐全”；交付等级约束结果，不自动增加架构、文档或流程。明确 feature、issue、spec 或 public contract 已选择方向时直接进入实现。
2. **只在方向真实开放时调用 Option Search；价值 claim 单独验收。** 满足 Kernel 的 material-fork/选错代价门槛，且用户要求 ideation/比较，或目标仍容许多个会形成不同用户行为、价值主张或系统边界的方向时，调用 `option-search`。已有使用数据、真实工作流、用户事实、支持记录、实际交互或最小行为 probe 可以支持价值判断；合成人格、Agent 偏好和漂亮 prototype 只能生成假设。明确方向不因缺少价值证据而自动 pivot；这不妨碍交付“实现了该能力”，但不能升级为“用户需要、值得扩展或方向已验证”。
3. **先找最近的正确范例，再推导最小 domain model。** 优先检查同仓库成熟路径、用户提供的成品、已批准设计或可信公开实现，提取用户行为、状态不变式、错误处理和验证方法，并明确本任务与它的差异；复用已被证明的 invariant，不复制视觉表面、代码或不适用的架构。找不到范例不是 blocker，也不要求创建参考文档。只对影响行为的概念确定 identity、关系、所有权、持久性和关键不变式；有状态资源按实际语义推导转换与恢复，不机械要求 CRUD。
4. **绑定真实后端、集成与调用方可见语义。** 仅在 claim 触发时明确 public interface、兼容、输入验证、身份/所有权/授权、持久性、状态转换、一致性/并发、retry/idempotency、外部失败、安全、性能或运维边界。public API 有多个可信解释时比较默认值、显式 opt-in、错误/清理与资源状态保持；无歧义时不制造矩阵，也不为假想未来预建平台层。若成品声称 server-backed、共享状态或真实集成，临时 seed 的内存数据、静态 mock、无验证字符串分派或只改变前端状态不能充当该语义完成的证据；本地单用户产品也不被机械要求登录或分布式机制。
5. **在 UI 是价值面时先冻结产品特定的视觉方向。** 从真实领域材料、信息优先级、品牌/现有设计系统、用户参考与反例中，形成最小但可观察的内容语气、信息层级、密度、typography/视觉身份、目标 viewport 和适用状态；高歧义时由 `option-search` 比较实质不同的信息架构/交互方向，选择后不把候选元素拼盘。若界面去掉 logo 和文案后可无差别套给无关产品，或用通用 hero/dashboard/card 模板代替领域主任务，就不能支持“高质量产品设计”的 claim。Brief 可以在对话或计划中，不强制新文件；Skill 只能提供候选，不能改变产品契约或自验收。
6. **先做代表最终质量的判别性 vertical slice。** 它从真实输入/交互穿过实际领域状态、主要逻辑以及产品声称的后端/持久化边界，到达用户可观察结果，并至少覆盖一个会否定路线的失败路径；优先关闭价值、集成或整体架构的最高信息风险。中间 mock 可用于局部开发，不能证明 slice 闭环。slice 只有通过匹配 Oracle 后才成为后续扩展的 golden implementation；若它证伪未冻结候选可 kill，若它证伪已冻结方向则停止并 re-contract，不能自行改题。
7. **沿 golden slice 扩展最小 critical journeys。** 从冻结能力、交付等级和 domain/state 语义选择能区分“可用产品”与“happy path demo”的旅程；只为具体失败路径增加 empty/missing、invalid/denied、retry/reload/restart 或 partial-failure。后续模块复用 slice 已验证的行为、错误和测试 invariant，不为表面一致复制组件，也不因已有代码而扩展 non-goal。若声称 comparison/compare/对比，必须在同一决策上下文真实比较契约数量和类型的对象；单个 ranking/recommendation 不能冒充 comparison。
8. **在最短真实反馈回路中实现。** 每次先关闭一个决定性未知量，再用与当前 claim 相称的 oracle 检查。局部测试可定位错误，但共享实现假设的测试不能单独证明最终能力；真实外部集成由最便宜的实际调用或契约 oracle 支持。只有能显著缩短重复反馈回路或让 Agent 直接观察核心行为时，才增加 CLI、脚本或 API 入口，不为“agent-friendly”给所有模块造第二套界面。
9. **对 UI-complete claim 使用真实 render/browser oracle。** 在真实运行时操作适用 journeys，检查可见结果、交互、状态反馈、目标 viewport、长内容及会否定 claim 的 console/request/runtime 失败；按真实 failure path 检查 empty/loading/error/recovery，而不是机械穷举状态。构建、类型检查、组件存在、代码 review 或静态截图不能单独证明交互完成。若交付还声称 product-grade 视觉质量，使用一个未主导该视觉实现的观察者，基于冻结方向和同状态真实截图指出会否定 claim 的具体问题，合并一轮高价值修复；只有关键失败仍在时才聚焦复验，不启动无界审美循环。非 UI 交付不触发 browser gate。
10. **以紧凑 Proof-of-Work 收口。** 使用 `drift-check` 核对实际 diff、交付等级和产品语义，然后在 PR、最终报告或既有项目载体中保留最小充分证据：启动/检查命令及关键输出、实际浏览器/API 路径、适用截图、console/network 状态、失败路径与已知限制。小任务不创建独立报告，截图也不能替代交互证据。只有当前 claim 包含价值/方向结论时才要求真实价值证据；否则区分“能力已交付”和“价值仍未建立”。只因具体风险升级全量测试、性能/安全/可达性检查或额外 review。

## 门禁

- `[AUTO]` 若核心 capability、重要 non-goal 或可信验收方法完全无法确定，阻断依赖该信息的实现。
- `[AUTO]` 若交付 claim 包含“真实用户需要/值得扩展/方向已验证”，但没有任何真实价值信号，相关价值 claim 保持 `NOT_ESTABLISHED`；不阻断方向已冻结的软件实现。
- `[RUNTIME]` 声称真实外部集成时需要实际集成/契约证据；声称交互 UI 完成时需要真实 render oracle 证据。环境确实阻止时可交付 `partial/ENV-BLOCKED` 与原始失败，不得宣称已验收完成。
- `[HUMAN]` 只在 Supervisor 定义的未授权语义、public/compatibility、凭据、生产/发布、不可逆状态、法律/隐私或 material/unbounded cost 边界等待决定。

固定技术栈、目录、文件名、CRUD 形状、viewport、模型、sub-agent 数量、review 轮次与 full-suite 本身都不是门禁。

## 完成判定

- 冻结的主要 capability 已从真实输入/交互贯通到用户可观察结果，而非只有局部模块或 happy path 存在；
- 实际交付没有低于冻结的交付等级；完整成品的核心旅程跨越它声称的真实前端、后端、持久状态或外部集成边界，mock/synthetic 部分均被披露；
- 对交付成立所必需的 domain identity、关系、状态转换与 critical journeys 已被实现和直接证据支持；
- representative slice 已由匹配 Oracle 通过后才被扩展；golden example 复用的是行为与 invariant，不是模板表面；
- comparison、server-backed、UI-complete 或 product-grade visual quality 等特殊 claim 符合其本身的语义与 Oracle 要求；
- 能区分能力交付与产品价值 claim；只有实际声称价值/方向成立时，才有相应真实用户、使用或行为证据；
- 关键错误和恢复语义与契约一致，没有静默成功、未授权产品扩张或把被阻断证据写成通过；
- 文档、测试、Git 和外部交付状态的报告与实际一致。

## 失败处理

保留失败命令、未通旅程和被阻 oracle 的证据；优先修复实现、缩小未知量或选择能以原 acceptance 重新验收的质量等价路径。不得为了让 demo “看起来可用”而加入未契约、未测试的 speculative runtime fallback；若 resilience/degradation 本身是用户要求的产品能力，则把它作为显式产品语义实现并验收。新路径改变 public behavior、数据/隐私边界、不可逆状态或资源承诺时进入 re-contract/HUMAN gate。

## 产物

- 存于请求、issue/plan/PR 或项目原生文档中的最小 capability contract；
- 与产品实际形态相称的 domain/state 语义和 critical journeys，不强制独立表格或指定文件；
- 通过后可供扩展的 representative slice/golden implementation，或其未通过的决定性证据；
- 可运行的产品工件与支持交付 claim 的决定性证据；
- 实际存在的局限、未验收部分和外部/Git 状态。
