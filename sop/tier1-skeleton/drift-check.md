# SOP-drift-check: 漂移检查(防跑偏 / scope creep)

- **层级**: tier1-skeleton
- **落实纪律**: P1(对照契约,越界即拦)
- **绑定骨架**: development
- **通用性档位**: U1(检查动作通用,需求集项目相关)
- **版本**: v1

## 触发条件

development 骨架实现过程中,每次提交(product)或每个里程碑(prototype)对照契约自查。

## 前置条件

- `spec/REQUIREMENTS.md` + `spec/NON_GOALS.md` 已定稿(`→ tier1-skeleton/write-contract.md`);
- 有一批待检查的改动(diff)。

## 依赖 SOP

→ tier0-core/no-fallback-review.md(漂移检查同时过零 fallback 审查)。

## 步骤

1. 对每处改动问:**"对应哪条 REQUIREMENT?"** 对不上=可疑的 scope creep,标记。
2. 问:**"有没有引入 NON_GOALS 里的东西?"** 越界即拦,要求移除或走变更流程改契约。
3. 问:**"有没有新增未声明的依赖/抽象层?"** agent 最爱顺手加抽象——需回到 `→ tier0-core/add-dependency.md` 补理由,否则拒。
4. 过 `→ tier0-core/no-fallback-review.md`。
5. 结论:全部改动可追溯到需求且无越界 → 放行;否则拦截并列出待处理项。

## 门禁

[REVIEW] product 每次提交扫 / prototype 里程碑扫。
[SCAN] 依赖方向单向、无循环(import 图扫描)。

## 完成判定

- 每处改动可映射到某条 REQUIREMENT;
- 无 NON_GOALS 越界、无未声明依赖/抽象(二值)。

## 失败处理

遵守 P3:改动对不上任何需求 → 拦截,要么删掉要么先改契约,不得"先留着说不定有用";检出 NON_GOALS 越界 → 拦截,不得"顺手做了就留下";发现循环依赖/打穿分层 → 拦截修复,不得"能跑就先不管架构"。

## 产物

一份漂移检查结论:改动-需求映射表 + 越界/未声明项清单 + 放行/拦截结论。
