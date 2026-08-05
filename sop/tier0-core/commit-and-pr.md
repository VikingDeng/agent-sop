# SOP-commit-and-pr: 提交与 PR

- **层级**: tier0-core
- **落实纪律**: P4(可追溯)
- **绑定骨架**: 无
- **通用性档位**: U1(假设用 git,不绑具体托管平台/CI)
- **版本**: v1

## 触发条件

一组代码变更完成、需要落成一次可追溯的提交或 PR 时。

## 前置条件

- 变更已本地自审;
- 已过 `→ tier0-core/no-fallback-review.md`;
- 每处改动能指认对应的需求/任务(P4 前提);
- 项目已 `git init` 且有远端(项目任务默认 GitHub 私有仓库为代码中枢,见科研骨架 §4.6;一次性/throwaway 脚本可免)。

## 依赖 SOP

→ tier0-core/no-fallback-review.md(提交前必过零 fallback 审查)。

## 步骤

1. 确认工作树干净度:`git status` 无遗漏;确认本次要提交的文件集合就是意图集合(无顺手夹带)。
2. 写 commit message,格式 `{type}: {做了什么 + 对应哪条需求/任务}`,type ∈ {feat/fix/refactor/docs/restructure/...};message 必须能回答"这次改动追溯到哪"。
3. 若改动跨越多个独立意图,拆成多个 commit,一 commit 一意图(便于回溯与回滚)。
4. 推分支 `{branch}`;开 PR,PR 描述含:变更摘要、对应需求/任务链接、验收方式、是否含破坏性变更。
5. 关键决策(架构/接口/取舍)若产生,记入项目 `{ADR/DECISIONS.md}`,PR 里引用。

## 门禁

[AUTO] 提交前 `git_dirty=false`(要提交的变更已全部 stage,无未跟踪的意图内文件遗漏);commit message 符合 `{type}: {...}` 规范。
[REVIEW] PR 至少能回答:每个改动对应哪条需求?有无未声明的依赖/抽象?
[REVIEW] 产出符合 → PROSE_STANDARD.md(commit message / PR 描述)。

## 完成判定

- 存在一个 commit/PR,其 message/描述可把每处改动追溯到需求或任务;
- `git log` 能看到该提交;PR 处于可评审状态。
二值可查(命令 + PR 状态)。

## 失败处理

遵守 P3:若无法把某处改动追溯到任何需求 → 停止提交,先补需求或删除该改动,不得"先合了再说";若 commit/push 因冲突或校验失败 → 报错并中止,由人处理,绝不 `--force` 覆盖或跳过校验(`--no-verify`)静默通过。

## 产物

一个可追溯的 commit / PR:含规范 message、需求映射、(如有)ADR 记录。
