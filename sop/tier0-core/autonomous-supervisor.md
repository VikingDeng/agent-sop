# SOP-autonomous-supervisor: 自主任务监督与成本感知编排

- **层级**: tier0-core
- **落实纪律**: P1(先冻结任务契约) P2(确定性验证与独立 Review) P3(失败显式升级,禁止静默 fallback) P4(工作包、证据、决策与 Git 结果可追溯)
- **绑定骨架**: 无
- **通用性档位**: U1(编排不变式跨项目通用;角色配置、命令和工具由运行环境以 `{参数}` 注入)
- **版本**: v1

## 触发条件

- `[信号自触发]` 用户给出需要调查、修改、验证或交付的目标时,Supervisor 进入本 SOP;
- `[显式]` 用户要求自主执行、多 Agent 编排、验证、Review 或完整 Git 交付时进入本 SOP。

## 前置条件

- 用户目标、当前 workspace 和可用工具可被识别;
- 能写出目标、non-goals、假设、授权范围和至少一个可观测验收标准;
- 项目级 Agent 指令文件、spec、测试或现有行为中至少有一种契约来源;
- 修改任务开始前已检查工作树,用户已有改动可被保留或安全隔离。

无法满足第二项时不得以“自主”为由猜测需求,应进入 mandatory human checkpoint。

## 依赖 SOP

→ tier0-core/build-oracle.md(独立验证)

→ tier0-core/no-fallback-review.md(失败与 escalation 路径审查)

→ tier0-core/commit-and-pr.md(用户要求 Git 交付时)

## 步骤

1. **冻结任务契约(P1)**:从用户目标、适用 spec、测试和项目指令提取 `GOALS`、`NON_GOALS`、假设、allowed/forbidden scope、验收标准和验证命令。每项验收标准必须能由命令、文件状态或明确 Review 判据得到 true/false。把该记录保存在任务产物、计划或最终证据中,不得只留在不可追溯的思考里。

2. **判定 checkpoint 类型**:
   - `AUTONOMOUS_CHECKPOINT`:目标明确;验收可由现有证据推出;修改限于已授权 workspace;操作可逆;不改变 public API、兼容承诺或产品语义;不引入重大生产依赖;不发布;不接触新凭据;不删除持久数据;不做不可逆迁移。用户发出任务本身即为方向授权,记录判定后继续,不得再问“是否开始”。
   - `INTERACTIVE_CHECKPOINT`:方向大体明确,但用户主动要求阶段同步,或存在非阻断的偏好信息可改善结果。汇报后继续执行已授权部分;不得把日常命令或常规 Review 交还用户。
   - `MANDATORY_HUMAN_CHECKPOINT`:存在两个以上同样合理但产品语义不同的方向;需要改变 public API/兼容承诺、引入重大生产依赖、访问或轮换凭据、生产发布、删除数据、不可逆迁移、无法预估的显著付费、法律/合规/隐私决策;现有契约与目标冲突;或缺少关键需求且继续只能猜。写清决策、选项、影响和所需证据后停止越权部分。
   自动 checkpoint 与人工 checkpoint 都是 P1 留痕;区别是方向是否已由任务及契约客观确定。PR 可承载异步人类终审,不要求实现过程中逐步等待。

3. **分类任务风险**:
   - `TRIVIAL`:目标明确、范围窄、风险低、真实调用路径已知,且单 Agent 直接完成成本更低。主 Agent 直接执行,仍运行最小必要验证。
   - `STANDARD`:多文件修改、不熟悉调用链、普通 Bug、局部功能、非显然行为变化或需要独立 Review。最多使用一个定向 explorer;按需使用一个 worker;由 verifier 跑真实检查;行为变化由一个独立 reviewer 审查;默认一次 repair-review loop。
   - `HIGH_RISK`:并发/协程、对象生命周期、锁/线程亲和性、认证授权、安全边界、持久化数据/迁移、public API、协议兼容、生产配置、不可逆操作、性能关键路径、资源所有权或架构依赖方向。主 Agent保留架构所有权,修改前定向调查,实现后独立 risk review;无可验证证据不得完成。
   若命中多个类别,采用最高风险类别并记录触发信号。

4. **生成可委派工作包**:每个工作包必须包含 `objective`、`allowed scope`、`forbidden scope`、`relevant files/modules`、`invariants`、`acceptance criteria`、`validation commands`、`escalation conditions`、`expected evidence`。验收或边界仍模糊时不得委派“修好整个项目”之类目标。

5. **成本感知路由**:
   - 使用能可靠完成工作包的最低成本语义角色:explorer(定向只读调查)、focused_worker(边界清楚的机械修改)、worker(普通跨文件实现)、verifier(真实构建/测试/lint/扫描)、reviewer(正确性/回归/错误处理/测试缺口)、risk_reviewer(并发/安全/生命周期/数据/协议/架构)。模型或工具映射由 `{AGENT_ADAPTER}` 提供,不属于本 SOP。
   - trivial 不机械委派;主 Agent 不重复 subagent 已完成的宽扫描;多个 Agent 不重复读取同一批大文件;昂贵角色不运行机械构建命令;同一文件同一时间只有一个 writer;默认最多 `{MAX_CONCURRENT_SUBAGENTS=2}` 个 subagent 并发。
   - verifier 与 reviewer 必须独立于被审实现路径;“使用了 subagent”本身不是质量证据。

6. **执行状态机(P3/P4)**:工作包只能按以下显式状态转换并留痕:

   ```text
   WORK_PACKAGE_ASSIGNED
   -> COMPLETED(evidence)
   or
   -> FAILED(reason, evidence)
   -> ESCALATED(from_role, to_role, reason, scope_delta, criteria_delta)
   ```

   escalation 必须记录原角色失败原因与证据、为何超出工作包或能力边界、升级角色、修改范围是否扩大、验收标准是否变化。同一失败包不得由同一低能力角色无界重试。显式、有证据的升级不是 P3 禁止的 fallback;未记录地换角色、跳过验证或改变成功定义才是 fallback。

7. **按所有权实施**:主 Agent 合并架构与最终决策;writer 只修改工作包允许的文件并保留用户改动。方向或验收标准发生物质变化时返回步骤 1 重新冻结契约,不得边做边猜。默认只进行一次 `implement -> verify -> review -> repair` 循环;再次失败由主 Agent诊断并决定显式 escalation 或报告阻塞。

8. **确定性验证与独立 Review(P2)**:严格按 `契约 -> 定向调查 -> 实现 -> 确定性验证 -> 独立 Review -> 修复 -> 重新验证 -> 证据汇总` 执行。真实命令退出码和输出是 source of truth。Reviewer 不修改被审对象;finding 必须含 severity、文件/符号或位置、失败路径/证据和最小修复。纯风格 finding 不阻断;高风险 finding 未解决不得交付。找不到独立 oracle 时明确记录“未能独立验证”,不得让实现自证。

9. **漂移与失败审查(P3/P4)**:把每处修改映射到契约目标或必要验证;检查 NON_GOALS 越界、静默降级、扫描失败当通过、reviewer 不可用默认通过、oracle 不存在时自证等路径。调用 `→ tier0-core/no-fallback-review.md`;违规计数非零则阻断。

10. **交付与报告**:用户要求 Git 交付时调用 `→ tier0-core/commit-and-pr.md`,不 force push、不绕过 hooks、不夹带无关改动。最终报告只包含完成内容、关键文件、实际运行的验证及结果、Review finding 与处理状态、剩余风险/阻塞、branch/commit/PR;省略内部 delegation 流水账。

## 门禁

- `[AUTO][阻断型]` 契约字段和每条二值验收标准存在,否则不得写实现;
- `[AUTO][阻断型]` checkpoint 类型与风险类别有可指认触发条件;
- `[SCAN][阻断型]` 同一文件无重叠 writer,并发 subagent 数不超过 `{MAX_CONCURRENT_SUBAGENTS}`;
- `[RUNTIME][阻断型]` `{VALIDATION_COMMANDS}` 全部记录 exit code;任一失败不得写成通过;
- `[REVIEW][阻断型]` 行为变化有独立 reviewer;HIGH_RISK 有 risk_reviewer 或明确记录“未完成独立风险审查”并阻断交付;
- `[REVIEW][阻断型]` 失败处理与 escalation 通过 `→ tier0-core/no-fallback-review.md`;
- `[HUMAN]` 仅在步骤 2 的 `MANDATORY_HUMAN_CHECKPOINT` 客观条件命中时启用。

## 完成判定

以下条件全部为 true 才完成:

- 契约、checkpoint 类型、风险类别和修改-目标映射可查;
- 所有委派工作包字段齐全,状态均为 `COMPLETED(evidence)` 或有显式阻塞记录;
- 所有声明执行的验证都有命令、exit code 和结果,失败项为零;
- STANDARD 行为变化或 HIGH_RISK 工作有独立 Review 结论,高严重度 finding 为零;
- no-fallback 违规点为零,或任务被明确阻断且未伪装完成;
- 最终报告与 Git 状态(如适用)可由本地命令或远端状态复核。

## 失败处理

遵守 P3:契约无法写成可测判据、授权包络无法客观判定或必须猜产品语义时,进入 `MANDATORY_HUMAN_CHECKPOINT` 并停止越权部分;工作包失败时记录 `FAILED(reason, evidence)`,只通过显式 `ESCALATED(...)` 升级,不得偷偷换角色、扩大范围或降低验收标准;验证失败、reviewer 不可用、oracle 缺失、扫描器崩溃、push/PR 失败均如实报错,不得跳过后宣称完成;不可恢复用户改动冲突时停止写入并列出冲突文件。

## 产物

- 一份可追溯任务契约与 checkpoint/风险分类记录;
- 零个或多个字段齐全的工作包及其状态/证据;
- 实现 diff、确定性验证结果、独立 Review 及 repair 记录;
- no-fallback/漂移结论;
- 最终证据摘要,以及用户要求时的 branch、commit 和 PR。
