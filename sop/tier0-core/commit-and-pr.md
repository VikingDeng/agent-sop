# SOP-commit-and-pr: 提交与 PR

- **层级**: tier0-core
- **落实纪律**: P4(可追溯)
- **绑定骨架**: 无
- **通用性档位**: U1(假设用 git,不绑具体托管平台/CI)
- **版本**: v2

## 触发条件

一组代码变更完成、需要落成一次可追溯的提交或 PR 时。

## 前置条件

- 变更已本地自审;
- 已过 `→ tier0-core/no-fallback-review.md`;
- 每处改动能指认对应的需求/任务(P4 前提);
- 项目已 `git init`;是否有远端由选定的 delivery mode 决定。local handoff 可无远端。

## 依赖 SOP

→ tier0-core/no-fallback-review.md(提交前检查静默失败、造假与未披露降级)。

## 步骤

1. 确认工作树干净度:`git status` 无遗漏;确认本次要提交的文件集合就是意图集合(无顺手夹带)。
2. 写 commit message,格式 `{type}: {做了什么 + 对应哪条需求/任务}`,type ∈ {feat/fix/refactor/docs/restructure/...};message 必须能回答"这次改动追溯到哪"。
3. 若改动跨越多个独立意图,拆成多个 commit,一 commit 一意图(便于回溯与回滚)。
4. 按任务选定且记录一种 delivery mode：`commit`、`branch push`、`PR`、`direct authorized push/merge` 或 `local handoff`。远端交付时推送 `{branch}` 或执行明确授权的 direct push/merge；PR 描述含变更摘要、需求/任务链接、验收方式、是否含破坏性变更。
5. 关键决策(架构/接口/取舍)若产生,记入项目 `{ADR/DECISIONS.md}`,PR 里引用。

## 门禁

[AUTO] 选定 `commit`/远端 delivery 时 `git_dirty=false`(要提交的变更已全部 stage,无未跟踪的意图内文件遗漏);commit message 符合 `{type}: {...}` 规范。`local handoff` 至少保留可追溯 diff/status 证据。
[REVIEW] PR 至少能回答:每个改动对应哪条需求?有无未声明的依赖/抽象?
[REVIEW] 产出符合 → [PROSE_STANDARD.md](../../PROSE_STANDARD.md)(commit message / PR 描述)。
[HUMAN] `direct authorized push/merge` 只有在用户明确授权时可用；未授权不得把本地 handoff 改成远端交付。

## 完成判定

- 选定的 delivery mode 已完成：commit/branch push/PR/direct authorized push/merge 有对应 Git/远端状态，或 local handoff 有可复核的工作树状态与 diff;
- 每处改动可追溯到需求或任务，且验收证据已记录。二值可查(命令 + 选定模式的状态)。

## 失败处理

遵守 P3:若无法把某处改动追溯到任何需求 → 停止交付,先补需求或移出交付范围,不得"先合了再说";若 commit/push/merge 因冲突或校验失败 → 报错并中止当前交付模式，语义明确且可验证时允许自主解决冲突并重新运行受影响检查。绝不 `--force` 覆盖或跳过校验(`--no-verify`)静默通过；需要改变 delivery mode 时重新记录选择。

## 产物

一个可追溯的 commit / PR:含规范 message、需求映射、(如有)ADR 记录。
