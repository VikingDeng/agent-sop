# SOP 03 — 开发流程

## 总流程

```
plan → research → implement → review → ready
```

agent 从用户的自然语言请求推断工作流,不要求用户显式说"plan/research/implement/review"。

## 各阶段要求

### 1. Plan(任务宽泛、含糊或高风险时)

- 先计划再执行。
- 明确:目标、成功标准、风险、最小可行步骤。
- 非平凡任务创建任务根:`bash ~/ops/claude-task.sh ensure "<task title>"`,状态文件放 `dev/active/<task>/`。

### 2. Research(缺事实/外部知识/文献/搜索时)

- 路由到 `researcher`,返回结构化笔记,不污染项目文件。
- 深度研究前先明确当前北星能力目标、指标与核心假设;缺目标时询问或建临时目标(标记 `[UNCERTAIN]`)。
- 目标驱动研究,避免想法驱动游荡。

### 3. Implement

- 交给 `creator` 执行。
- 偏好**最小可逆变更**,保持动量。
- 状态文件保持更新(`plan.md` / `context.md` / `tasks.md`)。

### 4. Review(工作量大/风险高/非平凡时)

- 跑 `critic`,再跑 `codex-reviewer`(独立第二意见)。
- 两道门禁任一低于 80 分 → 任务不算 ready,修复后重审。
- 声称完成前先验证(见 SOP 05)。

## 恢复陈旧工作

- 用 `/catchup` 内部恢复上下文后再继续。
- 需要压缩或归因时用 `/changelog`。

## 操作原则

- 验证后再声称完成;不确定处显式标记 `[UNCERTAIN]`。
- 被纠正或发现持久偏好时,追加简短 `[LEARN:<category>]` 笔记到 `MEMORY.md`。
- 独立审视有益时,主动走 critic + codex-reviewer,而不是等用户要求。
- 数据质量、归因、可复现性、安全、提供商路由不明时:停下并报告不确定性(黄金法则)。
