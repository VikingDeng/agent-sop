# SOP 库索引(可组合规程)

> SOP = 一段可复用的、agent 可执行的规程。三层组织,SOP 之间可互相调用(见"依赖")。
> 每条 SOP 用 _TEMPLATE.md 结构;每条必须映射到 ../PRINCIPLES.md 的纪律。
> **组织判据不是"分类整齐",而是"每条 SOP 都是四条纪律的实例化"。**
>
> `tier1-skeleton/research-execution-grill.md` 当前 SOP 版本为 **v7**，默认按 proposal
> claim 自适应选择证据、oracle 与 gate。`research-execution-grill-v3 / schema v3`
> 是显式选择的 signed strict profile；历史 schema v1/v2 仅可匹配显式审计。
> `tier1-skeleton/run-experiment.md` 当前版本为 **v8**，默认以真实运行和 claim-matched
> evidence 验收；只有项目选择 strict v3 时才要求 exact signed authorization。
> `tier0-core/lock-env.md` 与 `reproduce-result.md` 当前为 **v2**：source/environment
> identity、locking、rebuild 与 replay independence 均按 claim 和可信 failure path 比例化，
> 不设 universal clean-tree、`ENV_LOCK`、clean-rebuild 或多 seed 门禁。
> 中间实验、数据流与 final table 使用 `tier1-skeleton/references/research-evidence-presentation.md`
> 的派生视图契约；它不要求新建 dashboard 或独立台账。
> `tier0-core/autonomous-supervisor.md` 当前为 **v19**，`build-oracle.md` 为 **v3**，
> `tier1-skeleton/run-development.md` 为 **v4**，`tier2-activity/option-search.md` 为 **v1**：
> 清楚小任务走快路，冻结方向直接执行，只有未冻结 material fork 才做候选碰撞与 decisive probe。
> Development v4 先验证 representative slice，通过后才作为 golden implementation 扩展；价值 claim 仍单独要求真实价值信号。

## Tier 0 — 核心横切(所有场景共用)

| SOP | 档位 | 落实纪律 | 被谁依赖 |
|---|---|---|---|
| tier0-core/autonomous-supervisor.md | U0 | P1 P2 P3 P4 | write-contract, run-competition, run-development |
| tier0-core/lock-env.md | U1 | P2 P3 P4 | add-dependency, fetch-assets, reproduce-result, run-experiment, release-version, ops-remote-compute |
| tier0-core/add-dependency.md | U1 | P1 P4 | fetch-assets, drift-check, release-version |
| tier0-core/build-oracle.md | U0 | P2 P3 | autonomous-supervisor, fetch-assets, profile-code, run-experiment, statistics-oracle, package-submission, build-local-proxy, research-execution-grill, run-competition, run-development, scientific-paper |
| tier0-core/no-fallback-review.md | U0 | P3 | autonomous-supervisor, commit-and-pr, drift-check, statistics-oracle, research-execution-grill, run-competition, run-development, ops-remote-compute |
| tier0-core/commit-and-pr.md | U1 | P4 | autonomous-supervisor, release-version, package-submission, ops-remote-compute |
| tier0-core/profile-code.md | U2 | P2 P4 | research-execution-grill |
| tier0-core/reproduce-result.md | U1 | P1 P2 P3 P4 | run-experiment, statistics-oracle, ops-deploy, scientific-paper |
| tier0-core/fetch-assets.md | U1 | P1 P3 P4 | — |

## Tier 1 — 骨架绑定

| SOP | 绑定骨架 | 档位 | 落实纪律 | 依赖 |
|---|---|---|---|---|
| tier1-skeleton/research-execution-grill.md | research | U2 | P1 P2 P3 P4 | build-oracle, no-fallback-review, profile-code, statistics-oracle |
| tier1-skeleton/run-experiment.md | research | U2 | P1 P2 P3 P4 | lock-env, build-oracle, reproduce-result, statistics-oracle, research-execution-grill, ops-remote-compute |
| tier1-skeleton/statistics-oracle.md | research | U1 | P1 P2 P3 P4 | build-oracle, reproduce-result, no-fallback-review |
| tier1-skeleton/contamination-check.md | research | U2 | P2 | — |
| tier1-skeleton/run-competition.md | competition / development(hackathon) | U1 | P1 P2 P3 P4 | autonomous-supervisor, build-oracle, no-fallback-review, build-local-proxy, package-submission, run-development |
| tier1-skeleton/package-submission.md | competition / development(hackathon) | U1 | P2 P3 P4 | build-oracle, commit-and-pr, maintain-patch-series |
| tier1-skeleton/build-local-proxy.md | competition | U2 | P2 P3 | build-oracle |
| tier1-skeleton/maintain-patch-series.md | competition | U1 | P4 | — |
| tier1-skeleton/write-contract.md | development | U1 | P1 | autonomous-supervisor |
| tier1-skeleton/drift-check.md | development | U1 | P1 | write-contract, add-dependency, no-fallback-review |
| tier1-skeleton/run-development.md | development | U1 | P1 P2 P3 P4 | autonomous-supervisor, write-contract, drift-check, build-oracle, no-fallback-review, option-search |
| tier1-skeleton/release-version.md | development | U1 | P4 | drift-check, lock-env, commit-and-pr, add-dependency |

## Tier 2 — 活动型(非项目工作)

> 这些工作不是"项目",不套骨架。运维类为**操作既有系统的规程手册**,不涉及在沙箱内起监听服务。

| SOP | 领域 | 档位 | 落实纪律 | 依赖 |
|---|---|---|---|---|
| tier2-activity/ops-deploy.md | 运维 | U1 | P1 P4 | reproduce-result |
| tier2-activity/ops-monitor-rollback.md | 运维 | U1 | P2 P3 | ops-incident |
| tier2-activity/ops-incident.md | 运维 | U0 | P3 P4 | — |
| tier2-activity/ops-remote-compute.md | 运维 | U1 | P1 P3 P4 | no-fallback-review, lock-env, commit-and-pr |
| tier2-activity/writing-tech-doc.md | 写作 | U0 | P1 P4 | — |
| tier2-activity/writing-report.md | 写作 | U0 | P2 P3 P4 | — |
| tier2-activity/scientific-paper.md | 写作 | U1 | P1 P2 P3 P4 | build-oracle, reproduce-result, contamination-check, statistics-oracle, PROSE_STANDARD |
| tier2-activity/research-investigation.md | 调研 | U0 | P1 P2 | — |
| tier2-activity/option-search.md | 方向搜索 | U0 | P1 P2 P3 P4 | — |

## 使用方式

1. 项目任务:引用 Kernel 与一个匹配真实交付面的 Domain Profile；只有 legacy 项目显式选择时才加载 ContestOS v1/overlay。
2. 非项目任务:直接选 tier2 SOP。
3. 一条 SOP 引用另一条时,按"依赖"字段调用,不复制内容。
4. 用户只给目标且授权范围清晰时,先走 `tier0-core/autonomous-supervisor.md`;它是唯一通用运行时决策源，负责契约、授权、验证、re-contract 与交付真相。成本/模型路由属于 Codex Adapter；Tier-1、legacy overlay、Skill 与 recipe 不得形成平行门禁。
