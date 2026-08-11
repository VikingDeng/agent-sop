# SOP-run-competition: 执行通用竞赛与黑客松

- **层级**: tier1-skeleton
- **落实纪律**: P1 P2 P3 P4
- **绑定骨架**: competition；development（产品型黑客松的成品开发）
- **通用性档位**: U1(竞赛机制通用；平台命令与阈值由项目注入)
- **版本**: v3

## 触发条件

- `[显式]` 用户要求参加、继续或交付一个有截止时间、规则、评测/评审和外部提交面的比赛；
- `[信号自触发]` 一个开发、科研或优化任务实际以比赛验收为终点，需要同时管理规则、评分反馈、提交预算或评委材料。

本 SOP 覆盖算法/交互题、数据榜单、Kernel/系统性能赛、agent/隐藏运行时评测、output-only/研究工件赛和产品型黑客松。它们不是互斥类型；一个比赛可同时命中多条执行路径。

## 前置条件

- 能取得一份当前权威规则；暂时取不到时，已把未知项及其可能影响标为 blocker，而不是凭记忆补齐；
- 用户要争取的结果已知，例如合法完赛、最高可行分数、进入奖项区、交付可演示成品或在期限内提交；
- 若要注册、接受规则、组队/合并队伍、上传、部署、公开发布或消耗付费/稀缺提交次数，已有相应授权，或这些动作被明确留在待授权边界外。

## 依赖 SOP

→ tier0-core/autonomous-supervisor.md(唯一通用运行时决策与授权边界)

→ tier0-core/build-oracle.md(按关键 claim 选择官方或独立验证证据)

→ tier0-core/no-fallback-review.md(防止通过改口径、隐藏失败或规则规避伪造成功)

→ tier1-skeleton/build-local-proxy.md(只有官方反馈昂贵、稀缺或不可本地运行时按需建立代理)

→ tier1-skeleton/package-submission.md(冻结并核验将要提交的准确工件；不执行外部提交)

→ tier1-skeleton/run-development.md(产品型黑客松需要交付完整产品时)

## 步骤

1. 冻结一份紧凑的 **contest contract**。它可以直接存在于用户请求、issue、计划、PR 或现有项目状态中，不要求新建固定文档；至少覆盖下列会改变执行的轴：
   - **判定轴**：binary verdict、绝对标量、多目标/Pareto、相对排名、评委 rubric 或 hybrid；
   - **反馈轴**：完整本地 evaluator、隐藏 judge、public/private leaderboard、interactive/adversarial、代码 review、现场 demo/问答，以及提交/查询次数；
   - **工件轴**：源码/patch/二进制、notebook、CSV/模型/output、agent/API、仓库/PR、运行中应用、硬件，以及视频/deck/form 等组合材料；
   - **环境轴**：语言/API、shape/dtype/精度、硬件、容器、时限/内存/token、网络、数据/外部模型许可、必用 partner technology；
   - **事件轴**：截止时间与时区、资格/队伍、规则接受、提交上限、final selection、演示/面试和赛后披露义务；
   - **外部动作包络**：允许使用的平台/账户、可自动执行的动作、提交/查询/付费上限、必须保留的 final reserve、凭据/数据/公开范围。未知但不影响当前安全工作的字段不制造空表。
2. 按轴组合最少充分的执行路径，而不是把比赛硬塞进四选一分类：
   - **算法、exact-output、interactive**：优先官方编译器/checker；对核心正确性使用与错误空间匹配且足够便宜的 reference、brute-force、property 或 differential oracle，并补边界与协议/timeout judge。只有存在具体 proof obligation、规则解释、tie-breaking、数值稳定性风险，或实现与验收共享同一错误路径时，才升级独立第二视角。不能写本地交互器时，明确哪些协议风险只会在线上暴露；
   - **数据/榜单**：固定 metric、split、允许数据与模型、泄漏边界、public/private 关系及 submission budget；探索集与 final holdout 分离，Kaggle 等 CLI 只执行平台动作；
   - **Kernel/系统优化**：先有正确基线和同口径 measurement，再优化；只有瓶颈或因果解释仍不确定时加载 nsys/ncu、rocprof、Ascend profiler 等平台工具，不把 profiler、roofline 或 patch series 当固定阶段；
   - **agent/隐藏运行时评测**：复用官方 `init → run → eval`、容器或 verifier，冻结 API/token/开发/测试时间与网络边界；长运行保留有效 checkpoint/partial output，避免在 timeout 时丢掉全部结果；
   - **产品型黑客松**：用 Development Profile 交付可运行产品，本 SOP 额外控制 eligibility、rubric、必用 SDK/MCP/partner tech、deploy/demo/video/deck/repo/form 和外部提交。评委分不是可伪装成二值测试的“客观分”；用 rubric-to-evidence 覆盖与真实演示证据降低不确定性；
   - **论文到 notebook、研究工件与 output-only**：验证方法/论文 fidelity、可执行性、输出格式与官方 evaluator；只有比赛 claim 需要时追加复现或统计证据。
3. 选择最早的高信息基线。官方 evaluator 能本地运行时直接使用，不重复造 proxy；核心正确性未知时先建最小 oracle；线上 pipeline/格式本身是主要未知、且授权包络允许一次廉价 smoke 时，可以早交 baseline；只有在线反馈慢、贵、噪声大或稀缺时才建 local surrogate/holdout。`local proxy first` 不是绝对顺序。
4. 进入 `build → verify → evaluate → learn` 循环：每轮只冻结当前候选、准备验证的假设、决定性证据和下一动作。多候选并行时隔离工件；核心算法/架构不变量未定时先关闭 critical-path uncertainty，再委派稳定实现。在线反馈回来后区分实现问题、代理失真、平台噪声和规则误读，不把 rank 的自然波动当代码回归。
5. 把探索预算、外部提交预算与 deadline 一起管理。反推平台上传/构建、视频处理、部署、人工检查与故障恢复所需时间，设置停止开发和冻结候选的 time reserve；在最终窗口之前提交或保存一个已验证的 last-known-good。只有多次提交、反馈稀缺、跨 session 或候选混淆风险真实存在时维护轻量 ledger；至少能回答“哪份工件、为什么交、占了多少预算、返回什么、下一次因此改变什么”。保留 final reserve，不为微小同向 delta 或无新信息的重复 probe 消耗它。
6. 用 `package-submission` 生成并核验候选 bundle。运行本地/官方验证的必须是将要提交的同一候选；如果平台会重新构建或运行，则验证其可按平台规则重建，而不是无条件要求 byte-identical rebuild、固定 SHA256 或 clean-tree 仪式。
7. **把打包与外部提交分开**。只有外部动作包络已明确时，才可在其中自主上传、提交、选择 final、部署或公开；一次授权可以覆盖包络内的后续提交，不逐次重复 HUMAN gate。超出平台、次数、final reserve、费用、数据或公开范围时停止越界动作，但继续准备可安全完成的候选。
8. 外部动作后保存平台 receipt/提交 ID、时间、确切工件身份及可取得的 score/verdict/rubric feedback；将有决策价值的 local↔official gap 回填到现有 issue/ledger/状态。单次提交不为形式创建完整目录树；live leaderboard 的当前 rank 必须标明时间，不能承诺其稳定。随机 tournament、对抗 judge、噪声 leaderboard 或人工 rubric 的单次反馈只是一条随机/主观观测；在影响候选选择时，记录其重复单位、可用预算和不确定性，不能把波动解释成确定改进。
9. 在以下任一条件满足时停止本轮策略并交付当前最佳合法成品：验收已满足；deadline/budget/reserve 到界；预计收益低于一次可靠验证或提交成本；相同失败不再降低不确定性；需要越出授权包络；规则或 evaluator 已无法支持更强 claim。停止刷分不等于丢弃已完成成品。

## 门禁

- `[BLOCK]` 工件违反官方规则、必需格式/技术/资源限制，或关键 correctness/verdict 已失败；
- `[BLOCK]` 用 hidden labels、泄漏、未允许数据/模型、替换 evaluator、伪造 demo、只优化不进入提交路径的代码，或改变评分口径来宣称成功；
- `[HUMAN]` 首次规则/法律条款接受、队伍合并、新凭据或超出现有凭据用途、公开发布、生产部署、个人/受控数据外发，以及未被现有包络覆盖的提交/付费/稀缺资源；授权一旦明确，包络内不重复设门；
- `[SIGNAL]` local↔official gap、评委反馈或运行环境差异暴露代理失真时，降低相应证据权重并修复 evaluator/策略，不用更多仪式掩盖失真；
- `[SIGNAL]` 随机、对抗或人工反馈不足以区分候选时，保持结论不确定并保护剩余预算；不得 cherry-pick 单次有利观测或用通用统计模板制造确定性；
- `[REVIEW]` 只有规则合规、弱 oracle、关键算法/架构、泄漏、评分路径或最终高价值提交存在具体失败模式时才安排第二视角。

## 完成判定

- 已交付比赛要求的完整工件，或在缺少外部授权时交付经核验、可直接提交的 bundle，并准确说明尚未执行的动作；
- 工件满足适用规则、格式、资源与 partner-technology 要求，关键 claim 有匹配证据且无 overclaim；
- 若已提交，可查到 receipt/ID 与实际平台状态；若是动态榜，只报告带时间的观察值；
- 提交次数、费用、final reserve、deadline 与凭据/数据/公开边界均未越权；
- last-known-good 的身份、最后可安全提交时间和 final selection 状态可查，不把“已上传候选”误报为“已选为最终提交”；
- 可从现有项目状态恢复当前最佳候选、决定性证据和下一动作；只有真实长周期风险才要求 durable state。

## 失败处理

规则来源冲突或会改变合法性时，停止受影响动作并请求人类裁决；不受影响的本地实现继续。官方 evaluator/平台失败时保留原错误与候选，不把“未评到”写成通过；可用质量等价路径复验，但不得自行更换成功定义。proxy 与线上长期失配时将其降级为探索信号，优先用剩余授权预算校准或报告不确定性，而不是继续盲刷。外部提交被拒绝时先区分格式、资格、平台故障和方案错误；修复后仍需沿用原规则与预算。到期或预算耗尽时交付当前最佳合法工件、证据和未决限制，不用仓促重构清零已有成果。

## 产物

始终只保留：紧凑 contest contract（或其现有载体）、当前最佳工件、支持其 verdict/score/rubric claim 的决定性证据，以及已发生外部动作的 receipt/状态。以下均为条件产物：多提交 ledger、local proxy/holdout、profile 原始记录、patch series、manifest、规则快照、demo/video/deck、跨 session 状态。未触发时不创建空目录、`N/A` 表或证明“没有做”的台账。
