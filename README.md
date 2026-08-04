# agent-sop

个人 agent 开发 SOP 体系仓库。**一个仓库容纳全部 SOP 文档 + 模板索引**,agent 开发时按任务类型遵守对应 SOP。

## 结构

```
agent-sop/
├── SOP/            # ★ 全部 SOP 文档(每份独立标准,含硬锚)
│   └── README.md   # 索引:类型/适用任务/版本/模板
├── templates/      # 模板仓库索引(按需配套)
└── README.md       # 本文件
```

## 当前 SOP

| SOP | 适用任务 | 模板 |
|---|---|---|
| [AI 科研架构标准 v1](SOP/contestos-ai-research-v1.md) | AI 科研/比赛项目(LLM/agent/RL/推理期/数据中心) | [contestos-starter](https://github.com/VikingDeng/contestos-starter) |

## 使用方式

1. 读 [SOP/README.md](SOP/README.md) 确定任务对应的 SOP。
2. 项目级 `CLAUDE.md` 一行引用对应 SOP 并遵守其硬锚。
3. 有配套模板的,clone 模板开工。

## 新增一个 SOP

1. 文档放 `SOP/<语义名>-v<版本>.md`(文件头部含:身份/适用范围/启用方式/版本来源)。
2. 更新 `SOP/README.md` 索引。
3. 需要模板骨架 → 建模板仓库(标记 Template Repository)→ 登记到 `templates/README.md`。
