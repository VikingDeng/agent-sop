# agent-sop

个人 agent 开发 SOP 与 skills 清单仓库。

**定位**:本机 agent 栈(Claude Code 运行时 + 各 agent)开发时遵守的规则与工具索引。任何 agent 接手本工作站任务时,应从这里读取约束,而不是凭记忆或猜测。

## 结构导航

```
agent-sop/
├── README.md          # 本文件:总览与导航
├── CLAUDE.md          # 仓库级 agent 规则(入口,先读)
├── SOP/               # 流程与规则文档(对 agent 的行为约束)
│   ├── README.md      # SOP 索引
│   ├── 01-workstation-governance.md  # 工作站治理:目录约定、安全
│   ├── 02-runtime-architecture.md    # agent 栈架构:角色分工、模型路由
│   ├── 03-development-workflow.md    # 开发流程:plan → research → implement → review
│   ├── 04-research-rules.md          # 研究规则:证据纪律、品味启发
│   ├── 05-coding-and-quality.md      # 编码规范与质量门禁
│   └── 06-code-project-development.md  # 代码与项目开发规范(草案)
├── standards/         # 任务层标准(按任务激活的深度规范)
│   ├── README.md      # 索引:适用范围/版本/启用条件
│   └── contestos-ai-research-v1.md   # AI 科研项目架构规范(施工蓝图,原样收录)
└── skills/            # skill 清单(只做索引,不镜像源码)
    └── INDEX.md       # 全部 skill:名称/领域/用途/触发场景
```

## 来源与同步

- 规则内容源自 `~/.claude/CLAUDE.md`(全局约束)与 `~/ops/claude/rules/`(细化规则)。
- `~/ops` 是工作站自动化的**唯一事实源**;本仓库是其对外文档化副本,供 agent 引用。
- 修改 SOP 时:优先改 `~/ops` 侧来源,再同步本仓库;或直接改本仓库并保持一致。
- skills 清单同步自 `~/ops/claude/skills/` 的 SKILL.md frontmatter。
- `standards/` 收录任务层标准(原样保留),源文件变更时重新复制并更新登记。

## 维护约定

- 文档保持精炼:一条规则讲清楚"为什么 + 怎么做"即可,不堆砌。
- 新增 skill 后更新 `skills/INDEX.md`。
- 变更 SOP 用 `[SOP]` 前缀的 commit message。
