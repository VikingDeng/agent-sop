# Legacy ContestOS skeletons

本目录保存三份 provenance-locked ContestOS v1 项目骨架。它们记录了历史来源和完整项目结构，但不再进入新任务的默认运行上下文。

新项目使用：

- 通用执行内核：[`autonomous-supervisor`](../sop/tier0-core/autonomous-supervisor.md)
- 0→1 开发：[`run-development`](../sop/tier1-skeleton/run-development.md)
- approved AI proposal 实现：[`research-execution-grill`](../sop/tier1-skeleton/research-execution-grill.md)
- 竞赛/benchmark/hackathon：[`run-competition`](../sop/tier1-skeleton/run-competition.md)

| Legacy source | 历史适用范围 | 状态 |
|---|---|---|
| [contestos-ai-research-v1.md](contestos-ai-research-v1.md) | AI research project skeleton | provenance-locked；explicit-only |
| [contestos-competition-v1.md](contestos-competition-v1.md) | performance/competition skeleton | provenance-locked；explicit-only |
| [contestos-development-v1.md](contestos-development-v1.md) | development project skeleton | provenance-locked；explicit-only |
| [contestos-adaptive-overlay-v2.md](contestos-adaptive-overlay-v2.md) | 将所选 v1 翻译到当前 Kernel/Profile 语义 | legacy compatibility overlay v2.4 |

## 显式启用

只有 closest project instructions 已经选择某份 v1，或用户要求复现/迁移 legacy workflow 时，项目级 `AGENTS.md` 才同时引用：

1. 当前 Kernel；
2. 当前 Domain Profile；
3. 所选 v1；
4. compatibility overlay。

冲突时以用户/项目 contract、当前 Kernel 和 Domain Profile 为准。不得编辑 v1 原件，也不得把 overlay 当成新的通用 authority。

## 迁移

迁移项目时，把仍有价值的 outcome、domain、evidence 和 risk requirements 写入项目 contract；把工具、模型、命令和目录细节写入项目/平台 adapter。完成后删除项目运行时对 v1/overlay 的引用，历史文件继续留在本目录供 provenance 查询。
