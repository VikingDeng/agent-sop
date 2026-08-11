# SOP 库索引(可组合规程)

> SOP = 一段可复用的、agent 可执行的规程。三层组织,SOP 之间可互相调用(见"依赖")。
> 每条 SOP 用 _TEMPLATE.md 结构;每条必须映射到 ../PRINCIPLES.md 的纪律。
> **组织判据不是"分类整齐",而是"每条 SOP 都是四条纪律的实例化"。**
>
> `tier1-skeleton/research-execution-grill.md` 当前 SOP 版本为 **v5**，默认按 proposal
> claim 自适应选择证据、oracle 与 gate。`research-execution-grill-v3 / schema v3`
> 是显式选择的 signed strict profile；历史 schema v1/v2 仅可匹配显式审计。
> `tier1-skeleton/run-experiment.md` 当前版本为 **v5**，默认以真实运行和 claim-matched
> evidence 验收；只有项目选择 strict v3 时才要求 exact signed authorization。

## Tier 0 — 核心横切(所有场景共用)

| SOP | 档位 | 落实纪律 | 被谁依赖 |
|---|---|---|---|
| tier0-core/autonomous-supervisor.md | U1 | P1 P2 P3 P4 | write-contract, run-competition |
| tier0-core/lock-env.md | U1 | P4 | add-dependency, fetch-assets, reproduce-result, run-experiment, release-version, ops-remote-compute |
| tier0-core/add-dependency.md | U1 | P1 P4 | fetch-assets, drift-check, release-version |
| tier0-core/build-oracle.md | U0 | P2 P3 | autonomous-supervisor, fetch-assets, profile-code, run-experiment, statistics-oracle, package-submission, build-local-proxy, research-execution-grill, run-competition, scientific-paper |
| tier0-core/no-fallback-review.md | U0 | P3 | autonomous-supervisor, commit-and-pr, drift-check, statistics-oracle, research-execution-grill, run-competition, ops-remote-compute |
| tier0-core/commit-and-pr.md | U1 | P4 | autonomous-supervisor, release-version, package-submission, ops-remote-compute |
| tier0-core/profile-code.md | U2 | P2 P4 | — |
| tier0-core/reproduce-result.md | U1 | P2 P4 | run-experiment, statistics-oracle, ops-deploy, scientific-paper |
| tier0-core/fetch-assets.md | U1 | P1 P3 P4 | — |

## Tier 1 — 骨架绑定

| SOP | 绑定骨架 | 档位 | 落实纪律 | 依赖 |
|---|---|---|---|---|
| tier1-skeleton/research-execution-grill.md | research | U2 | P1 P2 P3 P4 | build-oracle, no-fallback-review |
| tier1-skeleton/run-experiment.md | research | U2 | P1 P2 P3 P4 | lock-env, build-oracle, reproduce-result, statistics-oracle, research-execution-grill |
| tier1-skeleton/statistics-oracle.md | research | U1 | P2 P3 P4 | build-oracle, reproduce-result, no-fallback-review |
| tier1-skeleton/contamination-check.md | research | U2 | P2 | — |
| tier1-skeleton/run-competition.md | competition / development(hackathon) | U1 | P1 P2 P3 P4 | autonomous-supervisor, build-oracle, no-fallback-review, build-local-proxy, package-submission |
| tier1-skeleton/package-submission.md | competition / development(hackathon) | U1 | P2 P3 P4 | build-oracle, commit-and-pr, maintain-patch-series |
| tier1-skeleton/build-local-proxy.md | competition | U2 | P2 P3 | build-oracle |
| tier1-skeleton/maintain-patch-series.md | competition | U1 | P4 | — |
| tier1-skeleton/write-contract.md | development | U1 | P1 | autonomous-supervisor |
| tier1-skeleton/drift-check.md | development | U1 | P1 | write-contract, add-dependency, no-fallback-review |
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

## 使用方式

1. 项目任务:选 skeleton 后,在项目级 `AGENTS.md` 引用相关 tier0/tier1 SOP。
2. 非项目任务:直接选 tier2 SOP。
3. 一条 SOP 引用另一条时,按"依赖"字段调用,不复制内容。
4. 用户只给目标且授权范围清晰时,先走 `tier0-core/autonomous-supervisor.md`;它是唯一通用运行时决策源,负责风险分类、checkpoint、成本路由、验证与 Review。Tier-1、骨架、overlay 与 recipe 只做领域专门化,固定 artifact/step/gate 不得与其形成平行门禁。
