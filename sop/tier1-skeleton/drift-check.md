# SOP-drift-check: 漂移检查(防跑偏 / scope creep)

- **层级**: tier1-skeleton
- **落实纪律**: P1(对照契约,越界即拦)
- **绑定骨架**: development
- **通用性档位**: U1(检查动作通用,需求集项目相关)
- **版本**: v2

## 触发条件

development 骨架实现过程中,每次提交(product)或每个里程碑(prototype)对照契约自查。

## 前置条件

- `spec/REQUIREMENTS.md` + `spec/NON_GOALS.md` 已定稿(`→ tier1-skeleton/write-contract.md`);
- 有一批待检查的改动(diff)。

## 依赖 SOP

→ tier1-skeleton/write-contract.md(漂移判断使用已冻结契约)。

→ tier0-core/add-dependency.md(新增依赖或抽象需先补理由与锁定记录)。

→ tier0-core/no-fallback-review.md(漂移检查同时审查静默失败与未披露降级)。

## 步骤

> 方向性判据(先读再查):drift-check 核对的是**方向**,不是"实现恰好等于规约"。实现**缺失**规约要求的内容(impl < spec)→ 补;实现**背离**规约(impl ≠ spec,行为矛盾)→ 修,并与需求方确认方向;实现**超出**规约(impl > spec,多了更严的默认值、额外的防御分支、更全的边界处理)→ **不算 drift,放行**。只有缺失与背离进违规计数,富余不进。理由:一个把合理富余判成违规的 gate 会逼 agent 删正确代码迁就规约,制造反向劣化。

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
