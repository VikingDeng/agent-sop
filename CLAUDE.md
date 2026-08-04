# CLAUDE.md — agent-sop 仓库规则

本仓库是个人 agent 开发 SOP 与 skills 清单。任何 agent 在此工作或引用本仓库时遵守以下规则。

## 入口

- 先读 `README.md` 了解结构,再按需读 `SOP/` 下对应文档。
- 需要了解可用 skill 时读 `skills/INDEX.md`,不要臆测 skill 名称或用法。

## 核心约束

1. **`~/ops` 是工作站事实源**:本仓库是文档化副本,二者冲突时以 `~/ops` 实际配置为准,并回报差异。
2. **先读规则再动手**:接手工作站相关任务时,先读 `SOP/01`(治理)与 `SOP/03`(流程),再执行。
3. **SOP 是行为约束,不是参考读物**:遵守 `SOP/05` 的质量门禁(critic + codex-reviewer,低于 80 分不视为 ready)。
4. **最小可逆变更**:优先小步、可回滚的修改。

## 变更本仓库

- 保持文档精炼;禁止把个人闲聊、临时记录写入仓库。
- 新增/删除 skill 时同步更新 `skills/INDEX.md`。
- commit message 约定:`[SOP]` 前缀表示 SOP 文档变更,`[skills]` 表示清单变更。

## 敏感信息

- 禁止提交任何真实密钥、token、cookie 或个人信息(见 `SOP/01`)。
