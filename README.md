# agent-sop

个人 agent 开发规范体系仓库。四个平行概念,组成完整的地基:

Codex 从仓库根目录 [AGENTS.md](AGENTS.md) 进入:它只做高频路由,先读纪律与方法论,再按任务加载匹配的 skeleton/SOP。个人级自主 Supervisor 模板与 Codex agent recipe 位于 [codex/](codex/README.md),不与仓库级规则混用。

## 四个概念

| 概念 | 位置 | 一句话 | 回答的问题 |
|---|---|---|---|
| **纪律(Principles)** | [PRINCIPLES.md](PRINCIPLES.md) | 四条核心纪律(P1 契约先行 / P2 独立 oracle / P3 显式适配、禁止静默降级 / P4 可追溯)+ 收纳判据 | **为什么**这么做 |
| **文字规范(Prose)** | [PROSE_STANDARD.md](PROSE_STANDARD.md) | 产人读文字的横切规范(反 AI 味/逻辑闭合/反中庸,双关门禁),与纪律层正交 | **怎么说** |
| **骨架(Skeletons)** | [skeletons/](skeletons/README.md) | 一个**项目**的完整结构标准(目录树 + 防腐职责 + 硬锚) | **项目长什么样** |
| **SOP(可组合规程)** | [sop/](sop/README.md) | 一段可复用的、agent 可执行的规程,三层组织、可互相调用 | **怎么做一件事** |

> 纪律是"为什么",文字规范是"怎么说",骨架是"项目长什么样",SOP 是"怎么做一件事"。

## 结构

```
agent-sop/
├── AGENTS.md              # Codex 仓库级薄 dispatcher
├── PRINCIPLES.md          # 四条核心纪律 + 收纳判据(全仓地基)
├── PROSE_STANDARD.md      # 文字产出规范 v2(横切:产人读文字时遵守)
├── SKILL-ADAPTERS.md      # 官方/维护者 Skill 与 SOP 的适配矩阵(不改变 SOP 权威)
├── skeletons/             # 项目骨架(3 份 v1 原件 + v2.2 兼容 overlay)
│   ├── README.md          # 骨架索引与 compatibility overlay 入口
│   └── contestos-adaptive-overlay-v2.md
├── sop/                   # 可组合规程库(三层)
│   ├── README.md          # 三层 INDEX + 依赖图 + 纪律映射
│   ├── _TEMPLATE.md       # 单条 SOP 统一模板
│   ├── tier0-core/        # 核心横切(全场景共用,9 条)
│   ├── tier1-skeleton/    # 骨架绑定(11 条)
│   └── tier2-activity/    # 非项目型工作:运维/写作/调研(8 条)
├── codex/                 # 个人模板与 custom-agent adapter
└── scripts/               # 仓库独立验证器
```

## 使用流程

1. **判断任务是不是"项目"**(有 src/、跨时间存在、有交付物):
   - **是** → 选骨架([skeletons/README.md](skeletons/README.md)),在项目级 `AGENTS.md` 引用相关 tier0/tier1 SOP。
   - **不是**(运维/写作/调研)→ 直接走 [sop/tier2-activity/](sop/README.md) 的活动型 SOP。
2. **所有情况都受 PRINCIPLES 约束**(任何 skeleton/SOP 必须落实至少一条纪律)。
3. **产出人读文字时受 PROSE_STANDARD 约束**(产文字的 SOP 在门禁引用它,一处定义全库复用)。
4. **需要自主编排时走 [autonomous-supervisor](sop/tier0-core/autonomous-supervisor.md)**:在授权包络内自动冻结契约并执行;真实方向分叉才进入 HUMAN gate。
5. **选 Skill 适配器时读 [SKILL-ADAPTERS.md](SKILL-ADAPTERS.md)**:Skill 是按需、可替换的能力层;不改变 SOP 的授权、路由、claim、HUMAN 边界、门禁或完成判定。
6. **实施已批准科研 proposal 前走 [research-execution-grill](sop/tier1-skeleton/research-execution-grill.md)**:不重新生成 idea；按 claim 选择真正需要的 oracle、pilot、风险边界和 scale 证据，不强迫所有 proposal 进入同一 gate 链。
   - 方法关键语义先形成最小 fidelity mapping；科学 run 无自动 runtime fallback，弱发现不替代原 claim。
   - 中间实验/数据流与最终表按 [research evidence presentation](sop/tier1-skeleton/references/research-evidence-presentation.md) 从 raw runs 派生；远程算力按 [ops-remote-compute](sop/tier2-activity/ops-remote-compute.md) 执行。

7. **选用任一 ContestOS v1 骨架时同时启用 [adaptive overlay v2.2](skeletons/contestos-adaptive-overlay-v2.md)**:它只覆盖运行时语义，明确解释 fallback、HUMAN checkpoint、环境参数与 claim/risk-triggered gates；v1 原件保持 provenance-locked。参加算法/交互、榜单、性能、hidden-runtime、研究工件或产品型黑客松时，再用 [run-competition](sop/tier1-skeleton/run-competition.md) 按真实赛制组合路径。

## 新增一个 SOP

1. 用 [sop/_TEMPLATE.md](sop/_TEMPLATE.md) 建文件,放到对应层级目录(`tier0-core` / `tier1-skeleton` / `tier2-activity`)。
2. 头部填"落实纪律"(必须映射到 PRINCIPLES 的某条,对不上则先补纪律)。
3. 更新 [sop/README.md](sop/README.md) 索引。

## 新增一个骨架

1. 文档放 `skeletons/<语义名>-v<版本>.md`,头部声明落实的纪律。
2. 更新 [skeletons/README.md](skeletons/README.md) 索引。
