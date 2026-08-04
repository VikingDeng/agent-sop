# SOP 02 — agent 栈架构

## 角色分工(v9 split)

| 角色 | 职责 | 约束 |
|---|---|---|
| `creator` | 写代码、论文、文档、实验 | 遵守质量规则 |
| `researcher` | 搜索、阅读、综合,返回结构化笔记 | 只读,不改项目文件 |
| `critic` | 严格只读质量审计,0-100 打分 | 不改文件 |
| `codex-reviewer` | 经本地 `codex` CLI 的独立第二意见 | 默认走 CRS 提供商路径 |

## 内部命令

| 命令 | 用途 |
|---|---|
| `/catchup` | 恢复过期上下文 |
| `/plan` | 创建任务计划与 active-task 文件 |
| `/review` | 运行 review 门禁 |
| `/changelog` | 压缩近期变更并归因 |

这些是实现细节。用户侧保持自然语言体验,agent 自行决定何时触发等价内部流程,不要求用户记住命令名。

## 模型路由

| 模型 | 用途 | 占比 |
|---|---|---|
| Sonnet | 日常执行 | ~90% |
| Opus | 架构、系统决策、深度推理、critic | 正确性/判断主导成本时 |
| Haiku | 简单格式化、分类、翻译、低风险样板 | — |
| Codex / GPT-5.4 | 独立第二意见、数学重推理、对抗反馈 | — |

路由原则:
- 常规编辑不升级 Opus;正确性或判断主导成本时升级。
- 日常 Claude 任务默认不走网关;`~/ops/run-claude-via-gateway.sh` 仅作为显式实验入口。

## Codex 政策

- Claude 与 Codex 保持两个原生 harness,不互相伪装。
- 本地 `codex` CLI 默认使用 CRS 提供商;除非用户要求或 CRS 不稳定,不切换。
- 默认不强制 Codex 走 LiteLLM/中转 API。
- 使用 `codex-reviewer` 时不覆盖提供商默认,除非首跑失败。
- 默认体验:Codex 是自动的隐藏第二大脑,不是用户需显式驱动的工具。

## 上下文卫生

- 偏好 `document and clear` 模式,避免上下文静默衰减。
- 活跃任务状态放在 `dev/active/<task>/` 的 `plan.md`、`context.md`、`tasks.md`。
- 非平凡任务先建任务根,managed helper:`bash ~/ops/claude-task.sh ensure "<task title>"`。
- 会话启动时,git 项目无活跃任务时可自动 bootstrap 默认会话任务。
