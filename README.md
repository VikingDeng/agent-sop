# agent-sop

面向 Codex/GPT Agent 的个人执行规范。目标不是用更多 checklist 替代模型能力，而是用一个薄、稳定、可审计的流程内核降低交付方差；领域能力由 Profile、外部 Skill 和真实 Oracle 在需要的节点补充。

## 分层架构

| 层 | 位置 | 只回答什么 | 不负责什么 |
|---|---|---|---|
| Principles | [PRINCIPLES.md](PRINCIPLES.md) | 为什么：契约、证据、失败诚实、比例化追溯 | 固定行动路径 |
| Kernel | [autonomous-supervisor.md](sop/tier0-core/autonomous-supervisor.md) | 所有任务怎样 RESOLVE→CONTRACT→EXECUTE→VERIFY→DELIVER | 技术栈、模型、领域方法 |
| Domain Profiles | [sop/tier1-skeleton/](sop/README.md) | development、AI research、competition 各自不可丢的结果语义 | Codex 路由、工具实现 |
| Codex Adapter | [codex/CODEX-ADAPTER.md](codex/CODEX-ADAPTER.md) | Sol/Terra/Luna、WCU、sub-agent、Hook、provenance、audit | 产品/科研完成判定 |
| Skills / MCP | [SKILL-ADAPTERS.md](SKILL-ADAPTERS.md) · [registry](skill-registry.yaml) | 外部、可替换的专门能力 | 改写契约、授权或阶段 |
| Oracles | [build-oracle.md](sop/tier0-core/build-oracle.md) 与项目工具 | 真实证据能否支持 claim | 自证或流程仪式 |

`PROSE_STANDARD.md` 是产出人读文字时的横切规范。`skeletons/` 保存 provenance-locked ContestOS v1 历史来源，只在 legacy 项目显式选择时使用，不进入新任务默认上下文。

## 默认入口

1. 所有实质任务使用 [执行 Kernel](sop/tier0-core/autonomous-supervisor.md)，冻结最小 outcome/non-goals/scope/evidence/authority contract。
2. 只加载一个与真实交付面匹配的 Profile：
   - 0→1 产品、服务、库、CLI、数据管线：[run-development](sop/tier1-skeleton/run-development.md)
   - 已批准 AI 顶会 proposal 的正确实现与实验：[research-execution-grill](sop/tier1-skeleton/research-execution-grill.md)
   - 竞赛、benchmark、leaderboard、hackathon：[run-competition](sop/tier1-skeleton/run-competition.md)
3. 只有任务确实跨域时组合 Profile，例如产品黑客松或研究工件赛。
4. Skill 由可观察能力缺口触发。稳定运行只允许 registry 中未过期的 `promoted` 能力隐式启用；受测候选与完整评测证据只保留在 source repository，未晋级候选不进入 runtime snapshot 或 `~/.codex/skills/`。
5. 验收始终回到项目真实 Oracle。Skill、模型、角色、文件存在、build、smoke 或自述不能替代 claim 所需证据。

## AI proposal → 实验

科研 Profile 的职责是把用户已批准 proposal 忠实、高效地实现，而不是重新生成一个更容易的 idea：

- 冻结原 claim、primary estimand、method 语义、baseline、数据/split、analysis、成功标准和正式预算；
- 建立 `proposal semantics → implementation → observable invariant → independent oracle` 的 method-fidelity mapping；
- 检查 baseline/tuning parity、必要的 negative control/ablation、holdout/judge protocol；
- evidence-bearing code fail fast，不写自动切 method/model/backend/device/data/metric/analysis 的 speculative runtime fallback；
- diagnostic/smoke/synthetic/mock/code-readiness 均 `paper_eligible=false`；
- raw runs 不可回写，过程视图和 final table 从 eligible evidence 确定性派生；
- inferential claim 按 [AI statistics oracle](sop/tier1-skeleton/statistics-oracle.md) 的数据生成过程、replication unit 与 estimand 验证；
- 远程资源由 project/local adapter 发现，通用 SOP 不包含默认服务器或 IP。

## Skill 选型

[`skill-registry.yaml`](skill-registry.yaml) 是严格 JSON 语法的 YAML 1.2 文件，为 source、commit/subpath/hash、license、依赖、副作用、触发与评测状态提供可机读字段。未核验的 exact bytes/license 必须显式为 `null` 并附 blocker，只有进入 `audited` 前才要求补齐。任何候选要相对强 GPT‑5.6 比较三臂：

```text
strong no-Skill baseline
vs minimal reminder
vs full pinned Skill
```

只有 Full Skill 在固定模型、effort、工具、checkpoint 和预算下，经重复盲评证明净提升且没有 authority/acceptance 回归，才能 `promoted`。运行时禁止用 `find-skills` 自动搜索、安装和组合未知 Skill。

首个完成的 Product UI 对照结果是一个 no-go：固定 Anthropic `frontend-design` Full Skill 低于 strong baseline 和一句精准 reminder，因此没有被默认安装。对照显示有效增益来自“从具体领域推导视觉身份并拒绝可互换的通用模板”这条结果约束；它已进入 [Development Profile v2](sop/tier1-skeleton/run-development.md)，而不是被伪装成一个已验证 Skill。完整评分和可复核产物见 [evaluation result](evaluations/frontend-design-v1/results/2026-08-12/blind-review.md)。

Development Profile v2 另完成了一次全新 `complete product` E2E：真实浏览器贯通 HTTP API、合法/非法状态转换、SQLite、审计时间线与进程重启，且保留本地单用户 non-goals，没有追加 auth、CI、容器或外部集成。可运行产品与局限见 [Development v2 E2E](evaluations/development-v2-e2e/2026-08-12/README.md)；这是一个正向实例，不是跨任务因果证明。

## 目录

```text
agent-sop/
├── AGENTS.md
├── PRINCIPLES.md
├── PROSE_STANDARD.md
├── SKILL-ADAPTERS.md
├── skill-registry.yaml
├── sop/
│   ├── tier0-core/        # 9 条通用/横切 SOP
│   ├── tier1-skeleton/    # 12 条 Domain Profile / project SOP
│   └── tier2-activity/    # 8 条活动型 SOP
├── codex/                 # Codex Adapter、roles、Hooks、安装与审计
├── skeletons/             # explicit-only legacy provenance
├── scripts/
└── tests/
```

## 维护与验证

新增或修改 SOP 时遵循 [SOP 方法论](sop/_METHODOLOGY.md)，更新 [索引](sop/README.md) 和版本。测试要验证真实层边界和证据语义，不能只断言同一句话被复制到多个文件。

```sh
python3 scripts/validate_sop_repo.py
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

这些检查证明结构和可执行支持代码一致；SOP 的真实增益还必须通过固定任务上的 no-SOP / Kernel / Profile E2E，以及胜出 Profile 上的 no-Skill / reminder / Skill 对照实验验证。

Legacy ContestOS 文件及迁移方式见 [skeletons/README.md](skeletons/README.md) 与 [compatibility overlay](skeletons/contestos-adaptive-overlay-v2.md)。
