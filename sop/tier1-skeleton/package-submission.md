# SOP-package-submission: 打包一次正式提交

- **层级**: tier1-skeleton
- **落实纪律**: P3(禁静默 fallback 骗分)+ P4(提交绑证据链)
- **绑定骨架**: competition
- **通用性档位**: U1(competition 骨架内 submissions/ 机制确定,平台格式参数化)
- **版本**: v2

## 触发条件

competition 骨架项目中,产生一次要提交到线上榜/评测机的正式提交时。

## 前置条件

- correctness gate 已 pass(`→ tier0-core/build-oracle.md`);
- git 干净(`git_dirty=false`);
- 已知本赛 code 形态 `{code_form}`(patch/clone/scratch)与提交格式 `{SUBMIT_FORMAT}`。

## 依赖 SOP

→ tier0-core/build-oracle.md(correctness gate)

→ tier0-core/commit-and-pr.md(提交前落成可追溯 commit)

→ tier1-skeleton/maintain-patch-series.md(patch/clone 形态提交的字节级重建依据)

## 步骤

1. 门槛校验:correctness=pass 且 `git_dirty=false`;任一不满足即中止,不产提交。
2. 生成提交产物到 `submissions/{sub_id}/submitted_files/`——**所见即所提**(本地跑分用的就是这份)。
3. 可重建校验:确认产物能从 `{git_sha} + {upstream_commit} + patches` 字节级重建(见 maintain-patch-series)。
4. 写 `manifest.json`:sub_id/timestamp/git_sha/git_dirty=false/code_form/upstream_commit/patches[]/local_score/profile_ref/idea_ref/status。
5. 记 `SUBMISSION_LEDGER.md` 一行:sub_id|时间|commit|code_form|本地分|榜分(待回填)|gap|correctness|idea|状态。
6. 提交后回填线上分与 gap;gap 异常大 → 判本地代理失真,进排查(不是可忽略噪声)。

## 门禁

[AUTO] `git_dirty=false` 且 `correctness=pass` 才允许进 `submissions/` 与 `results/`。
[SCAN] 产物可从 sha+upstream+patches 重建;submitted_files 与本地跑分产物一致。

## 完成判定

- `submissions/{sub_id}/` 含 manifest + submitted_files + local_score;
- LEDGER 有对应行;
- 产物可重建(二值)。

## 失败处理

遵守 P3:kernel/解法禁 `if not supported: fallback to slow/torch path`——静默回退慢路径=分数造假(本地代理测不到真实提交路径),命中即作废;correctness=FAIL 的提交作废、不占正式行、不进 results/;`git_dirty=true` → 中止提交;本地分与提交产物不同源 → 判台账失效,禁止"本地跑一版提交另一版"。

## 产物

`submissions/{sub_id}/`:manifest.json + submitted_files/ + local_score.json + IDEA.md;LEDGER 新增一行。
