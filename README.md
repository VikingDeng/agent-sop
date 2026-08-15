# agent-sop

面向 Codex/GPT Agent 的个人执行规范。目标不是用更多 checklist 替代模型能力，而是用一个薄、稳定、可删除的执行内核降低交付方差：明确任务保持快，开放任务先提高方向质量，已批准研究则保持方法语义。Profile、Skill、Hook 和多 Agent 都只是候选机制；没有对强原生 Codex 的受控净增益就不进稳定运行时。

## 分层架构

| 层 | 位置 | 只回答什么 | 不负责什么 |
|---|---|---|---|
| Principles | [PRINCIPLES.md](PRINCIPLES.md) | 为什么：契约、证据、失败诚实、比例化追溯 | 固定行动路径 |
| Kernel | [autonomous-supervisor.md](sop/tier0-core/autonomous-supervisor.md) | 所有任务怎样 RESOLVE→CONTRACT→EXECUTE→VERIFY→DELIVER | 技术栈、模型、领域方法 |
| Domain Profiles | [sop/tier1-skeleton/](sop/README.md) | development、AI research、competition 各自不可丢的结果语义 | Codex 路由、工具实现 |
| Codex Adapter | [codex/CODEX-ADAPTER.md](codex/CODEX-ADAPTER.md) | 原生 HUMAN 交互、Sol/Terra/Luna、WCU、sub-agent、Hook、provenance、audit | 产品/科研完成判定 |
| Skills / MCP | [SKILL-ADAPTERS.md](SKILL-ADAPTERS.md) · [registry](skill-registry.yaml) | 外部、可替换的专门能力 | 改写契约、授权或阶段 |
| Oracles | [build-oracle.md](sop/tier0-core/build-oracle.md) 与项目工具 | 真实证据能否支持 claim | 自证或流程仪式 |

`PROSE_STANDARD.md` 是产出人读文字时的横切规范。`skeletons/` 保存 provenance-locked ContestOS v1 历史来源，只在 legacy 项目显式选择时使用，不进入新任务默认上下文。

## 默认入口

1. 所有实质任务使用 [执行 Kernel](sop/tier0-core/autonomous-supervisor.md)，冻结最小 outcome/non-goals/scope/evidence/authority contract，再按真实不确定性路由：
   - 每次请求先静默做 Requirement Judgment：事实由工具调查，安全默认由 Agent 采用，实现在契约内自主决定；只有两个以上可信解释没有占优安全默认、证据/probe 无法消解、选择会改变契约/边界且阻断受影响路径的下一可逆动作时，才询问用户，不显示默认问卷或内部分类。
   - 明确小任务：直接修改、聚焦验证、检查 diff；不生成候选、Durable Goal 或无关文档。
   - 明确 request/issue/spec/已批准 proposal：保持方向，直接执行；不因实现困难自动重开 ideation。
   - 开放方向：只在选错会主导成本时调用 [Option Search](sop/tier2-activity/option-search.md)，用核心语义差异、collision/falsifier 和 decisive probe 决定下一个可逆 slice。
2. 只加载一个与真实交付面匹配的 Profile：
   - 0→1 产品、服务、库、CLI、数据管线：[run-development](sop/tier1-skeleton/run-development.md)
   - 已批准 AI 顶会 proposal 的正确实现与实验：[research-execution-grill](sop/tier1-skeleton/research-execution-grill.md)
   - 竞赛、benchmark、leaderboard、hackathon：[run-competition](sop/tier1-skeleton/run-competition.md)
3. 只有任务确实跨域时组合 Profile，例如产品黑客松或研究工件赛。
4. Skill 由可观察能力缺口触发。稳定运行只允许 registry 中未过期的 `promoted` 能力隐式启用；其他候选只能用于显式选型实验。
5. 验收始终回到项目真实 Oracle。Skill、模型、角色、文件存在、build、smoke 或自述不能替代 claim 所需证据。

## 开放质量升级的验收方式

本仓不把“增加了 SOP 文本”当作能力升级。[开放质量 v1 评测合同](evaluations/open-quality-v1/README.md) 冻结了 `strong native Codex / current SOP / candidate SOP` 三臂、产品/研究 idea/已批准研究/简单任务四个 strata 与 routing 边界例；四个 pilot outcome bundle 已物理化并通过起点/负向 Oracle，其余 promotion fixture 仍须物理化，所有真实运行还必须绑定 Oracle、盲评、用户纠正与返工、WCU 和方差并交由独立 authority 裁决。[进化目标与 Todo](EVOLUTION.md) 记录当前事实、blocker 和下一判别动作，不形成第二运行时 authority。当前 Development v4、Option Search v1 和 Adapter v6 都是待评 candidate，不得因结构测试通过就声称已有净增益。

Codex App 的日常开发、竞赛与已批准 proposal 工程建议安装 `terra-supervisor`：Terra/high 负责前台语义与裁决，Luna 承担有直接 Oracle 的大块执行，Sol 只在持续高判断密度或具体高风险处窄调用。`preserve` 仍是安装器的安全默认，不会静默改现有模型；显式切换与运行时审计命令见 [Codex adapter](codex/README.md)。

显式长程任务可以使用 Codex 原生 goal 保存稳定目标；只有真实跨 task/session 或外部调度时才保存最小 continuity record。外部 scheduler 只接管已经 contract-ready、oracle-ready、state-ready 且 decomposition-ready 的执行生命周期，不能替代方向选择、验收或授权。默认不安装完整 ideation/compound 工作流；外部 Skill 仍按可测净增益单独评估，SOP 只吸收有直接 failure path 的最小机制。

## AI proposal → 实验

边界是：`idea 尚未批准 → Option Search`；`proposal 已批准 → Research Execution`。科研 Profile 的职责是把用户已批准 proposal 忠实、高效地实现，而不是重新生成一个更容易的 idea：

- 冻结原 claim、primary estimand、method 语义、baseline、数据/split、analysis、成功标准和正式预算；
- 建立 `proposal semantics → implementation → observable invariant → independent oracle` 的 method-fidelity mapping；
- 检查 baseline/tuning parity、必要的 negative control/ablation、holdout/judge protocol；
- evidence-bearing code fail fast，不写自动切 method/model/backend/device/data/metric/analysis 的 speculative runtime fallback；
- diagnostic/smoke/synthetic/mock/code-readiness 均 `paper_eligible=false`；
- raw runs 不可回写，过程视图和 final table 从 eligible evidence 确定性派生；
- source/environment identity、locking、rebuild 与 replay independence 按 claim 风险和具体共享错误路径比例化，不设 universal clean-tree、`ENV_LOCK` 或 clean-rebuild gate；
- inferential claim 按 [AI statistics oracle](sop/tier1-skeleton/statistics-oracle.md) 的数据生成过程、replication unit 与 estimand 验证；
- 远程资源由 project/local adapter 发现，通用 SOP 不包含默认服务器或 IP。

## Skill 选型

[`skill-registry.yaml`](skill-registry.yaml) 是严格 JSON 语法的 YAML 1.2 文件，为 source、commit/subpath/hash、license、依赖、副作用、触发与评测状态提供可机读字段。候选可以分别处于 declared、audited 或 evaluated，但当前仍没有 promoted 能力；未核验的 exact bytes/license 必须显式为 `null` 并附 blocker，只有进入 `audited` 前才要求补齐。任何候选要相对强 GPT‑5.6 比较三臂：

```text
strong no-Skill baseline
vs minimal reminder
vs full pinned Skill
```

只有 Full Skill 在固定模型、effort、工具、checkpoint 和预算下，经重复盲评证明净提升且没有 authority/acceptance 回归，才能 `promoted`。运行时禁止用 `find-skills` 自动搜索、安装和组合未知 Skill。“local”只描述文件位置，不描述来源或质量；catalog、audited、installed/enabled 与 promoted 是四种不同事实。备份和退役 Skill 必须放在 Codex 不扫描的位置，同名用户副本与插件副本只保留一个预期来源。

首轮外部源码审计与 Trail of Bits property-based testing 的 3×3 负向 pilot 见 [round 1 evidence](skill-evaluations/round1-2026-08-12.md)：三臂均命中 8/8 初始隐藏检查，完整 Skill 在该轴没有优势且盲评低于两句提醒；由于评测协议和兼容性证据仍有缺口，该候选保持 audited 而非 evaluated，更没有进入稳定集。

## 目录

```text
agent-sop/
├── AGENTS.md
├── EVOLUTION.md          # open-quality durable goal, evidence state, and Todo
├── PRINCIPLES.md
├── PROSE_STANDARD.md
├── SKILL-ADAPTERS.md
├── skill-registry.yaml
├── skill-evaluations/     # external Skill source audits and controlled net-lift results
├── evaluations/           # SOP 对照合同、fixtures 与可机读结果
├── sop/
│   ├── tier0-core/        # 9 条通用/横切 SOP
│   ├── tier1-skeleton/    # 12 条 Domain Profile / project SOP
│   └── tier2-activity/    # 9 条活动型 SOP
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
