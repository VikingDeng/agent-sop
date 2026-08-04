# SOP 索引

> 本目录存放**全部 SOP 文档**。每个 SOP 是一份独立标准:适用某类任务,含硬锚(不可违反)。
> 新增 SOP:`SOP/<语义名>-v<版本>.md`,并在此登记一行。

| SOP | 类型 | 适用任务 | 版本 | 硬锚 | 模板 |
|---|---|---|---|---|---|
| [contestos-ai-research-v1.md](contestos-ai-research-v1.md) | AI 科研 | LLM / agent / RL / 推理期方法 / 数据中心(含比赛项目) | v1 | §6 | [contestos-starter](https://github.com/VikingDeng/contestos-starter) |

## 使用方式

1. 确定任务类型 → 读对应的 SOP(多个相关时全部读)。
2. 项目级 `CLAUDE.md` 一行引用:`开发前先读 <SOP 文件名> 并遵守其硬锚`。
3. 有配套模板仓库的,clone 模板开工。

## 维护约定

- 每个 SOP 在文件头部维护:文档身份 / 适用范围 / 启用方式 / 版本与来源。
- 源文件变更后重新同步,保持 sha256 一致。
