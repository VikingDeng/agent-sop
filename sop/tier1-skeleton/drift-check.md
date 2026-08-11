# SOP-drift-check: 漂移检查（防跑偏与无收益扩张）

- **层级**: tier1-skeleton
- **落实纪律**: P1(对照结果契约与 non-goals)
- **绑定骨架**: development
- **通用性档位**: U1(方向判据通用,检查载体与频率按风险决定)
- **版本**: v3

## 触发条件

development 实现到达有意义的 integration/handoff/delivery 边界，或 diff 出现可信的 scope creep 信号时执行。小型局部修复可把该判断合并进最终 diff 检查；不要求每次 commit 生成独立 drift review。

## 前置条件

- 有一个可定位的结果契约；它可以在请求、计划、issue、PR、测试或 formal spec 中，不要求固定文件名；
- 有一批值得判断方向的实际改动或明确设计方案。

## 依赖 SOP

→ tier1-skeleton/write-contract.md（提供与规模相称的冻结契约）。

→ tier0-core/add-dependency.md（新增依赖或持久抽象且需要判断代价时使用）。

→ tier0-core/no-fallback-review.md（改动触及错误、缺失能力或降级路径时使用）。

## 步骤

1. 从当前契约提取目标行为、non-goals、允许范围、public contract 与不可接受结果，不把推荐目录或旧计划步骤误当成产品语义。
2. 检查 diff 是否直接推进目标，或是否为实现目标所必要。无需把每行代码机械映射到 REQUIREMENT 编号；需要解释的是新增产品语义、依赖、持久抽象、运维负担和明显扩大的测试/文档面。
3. 检查是否改变 non-goals、public behavior、兼容承诺、数据/隐私边界或资源承诺。真实语义改变必须回到契约/HUMAN 边界；普通实现策略变化不需要 re-contract。
4. 对额外防御、边界处理和抽象做比例判断：若存在具体失败路径、成本与潜在伤害相称、没有新增未授权语义或长期负担，可保留；若只是“以后也许有用”、复制框架、增加固定 gate 或让 guardrail 接近主体工作量，则删除或缩小。
5. 只在触发条件成立时调用依赖 SOP：新增依赖评估其真实必要性；改变 error/fallback 路径检查是否静默降级；架构边界确有侵蚀风险时才运行依赖图等 scanner。
6. 在现有 plan、PR 或最终交付中给出简洁结论：无漂移，或列出具体偏离、失败场景和最小修复。除非项目需要长期审计，不创建映射表或独立报告文件。

## 门禁

只阻断会造成以下结果的改动：背离冻结目标、进入明确 non-goal、未经授权改变 public/compatibility/data boundary、引入无正当收益的持久复杂度，或隐藏失败/降低 acceptance。

检查频率、映射表、review、依赖扫描、全量测试和 named artifact 不单独构成门禁；它们只有在当前 diff 的 claim 或风险需要时才适用。

## 完成判定

- 当前 diff 的产品语义与冻结契约一致，必要实现和合理防御有清楚理由；
- 没有进入 non-goals、未授权 public change 或无收益的依赖/抽象/gate；
- 发现的阻塞偏离已最小修复或进入真实 re-contract，非阻塞 hardening 没有扩大本次 acceptance。

## 失败处理

发现漂移时先移除或缩小无关改动；确有用户价值但会改变语义的方向进入 re-contract，不以“已经写完”为理由保留。若契约本身不足以判断，补充最小语义而不是补齐整套 spec。若 scanner/reviewer 只给出品味建议或无法描述具体失败路径，不把它升级为阻塞 gate。

## 产物

嵌入现有 plan、PR 或最终交付的一段漂移结论，以及实际需要处理的具体偏离；默认不新增映射表、审计日志或 checkpoint 文件。
