# 项目骨架索引(Skeletons)

> 骨架 = 一个**项目**的完整结构标准(目录树 + 防腐职责 + 硬锚)。跨时间存在、有 src/ 有交付物。
> 与 SOP 的区别:骨架是"项目长什么样",SOP 是"怎么正确做一件事"。SOP 见 ../sop/。
> 三骨架共用地基见 ../PRINCIPLES.md。

三份 `contestos-*-v1.md` 是带版本与来源身份的 provenance-locked 原件,不得在原文件上叠加运行时规则。选中任一 v1 时，必须同时启用 [ContestOS adaptive operational overlay v2](contestos-adaptive-overlay-v2.md)：它明确 supersede 冲突的 v1 runtime wording，但不改写 v1 硬锚、来源声明或原文件。`autonomous-supervisor` 是通用依赖；v2 overlay 是 ContestOS 的 active runtime authority。

项目启用骨架时,在项目级 Agent 指令文件中引用:Codex 使用 `AGENTS.md`,Claude 使用 `CLAUDE.md`。v1 原件中专指 `CLAUDE.md` 的历史启用文字保留以维护来源完整性。

启用模板：项目级指令同时引用所选 `contestos-*-v1.md` 与 `contestos-adaptive-overlay-v2.md`;若两者运行时语义冲突，以 v2 overlay 为准。

| 骨架 | 适用 | 落实纪律 | 硬锚 |
|---|---|---|---|
| [contestos-ai-research-v1.md](contestos-ai-research-v1.md) | AI 科研:LLM/agent/RL/推理期/数据中心 | P1-P4 | §6 |
| [contestos-competition-v1.md](contestos-competition-v1.md) | 有客观分且可本地代理的竞赛 | P1-P4 | §8 |
| [contestos-development-v1.md](contestos-development-v1.md) | 高质量项目交付(库/服务/CLI/管线/infra组件/应用/黑客松MVP) | P1-P4 | §7 |
| [contestos-adaptive-overlay-v2.md](contestos-adaptive-overlay-v2.md) | 选中任一 ContestOS v1 时的 active runtime overlay | P1-P4 | supersedes conflicting v1 runtime wording; preserves v1 hard anchors |

## 选骨架

- 做实验/验证方法 → research
- 打有客观分的比赛 → competition
- 交付一个项目(含黑客松) → development
- **不是项目(运维/写作/调研)→ 不用骨架,走 ../sop/tier2-activity/**
