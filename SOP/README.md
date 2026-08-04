# SOP 索引

对 agent 的行为约束,按主题组织。阅读顺序建议:01 → 02 → 03 → 05(日常开发),04(研究类任务)。

| 文档 | 主题 | 一句话说明 |
|---|---|---|
| [01-workstation-governance.md](01-workstation-governance.md) | 工作站治理 | 目录约定、事实源、安全边界、可重建性 |
| [02-runtime-architecture.md](02-runtime-architecture.md) | agent 栈架构 | 角色分工(creator/researcher/critic/codex-reviewer)、模型路由、内部命令 |
| [03-development-workflow.md](03-development-workflow.md) | 开发流程 | plan → research → implement → review;任务状态管理 |
| [04-research-rules.md](04-research-rules.md) | 研究规则 | 证据纪律、来源纪律、研究品味启发 |
| [05-coding-and-quality.md](05-coding-and-quality.md) | 编码与质量 | 最小 diff、验证纪律、review 门禁、安全默认 |

## 内部命令速查

| 命令 | 用途 |
|---|---|
| `/plan` | 任务计划与 active-task 文件 |
| `/catchup` | 恢复过期上下文 |
| `/review` | 运行 review 门禁 |
| `/changelog` | 压缩近期变更并归因 |

这些是实现细节,日常用自然语言即可,agent 自行决定何时触发等价内部流程。
