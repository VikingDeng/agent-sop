# SOP-run-experiment: 运行一次可信实验

- **层级**: tier1-skeleton
- **落实纪律**: P1(假设先注册)+ P2(独立 oracle 判正确 + 上报干净重跑)+ P3(指标算不出/预算触顶即硬失败)+ P4(结果与预算与证伪决策可追溯)
- **绑定骨架**: research
- **通用性档位**: U2(指标/数据集/模型绑具体研究,需项目注入)
- **版本**: v4

## 触发条件

research 骨架项目中,需要跑一次实验产出用于决策/汇报的结果时。

## 前置条件

- 假设已预注册到 `{HYPOTHESIS_LEDGER}`(要验证什么、预期方向、成功判据),防事后编故事;
- 已批准 proposal 已按 `→ tier1-skeleton/research-execution-grill.md` 转成 schema v3 `{GRILL_ARTIFACT}`;pre-implementation/Phase 0 必须持有 exact `phase0_launch` signed final authorization,物质性扩容必须持有 exact `scale_launch` signed final authorization;
- 环境已按 `→ tier0-core/lock-env.md` 锁定;
- 正确性 oracle 已按 `→ tier0-core/build-oracle.md` 就位;
- **执行位置已定**:实验在远程服务器执行(科研骨架 §4.6,本机禁止跑实验),契约阶段已确认执行机或至少已记录资源需求;
- **算力预算已声明**:本次实验(或实验批次)的预算上限 {BUDGET} 已写入项目声明处(如 conf/ 或 docs/),至少含 gpu_hours 上限、token 上限之一;无声明上限 → 停,先与需求方确认预算,不得"先跑着看"(P1 契约先行的成本侧)。

## 依赖 SOP

→ tier0-core/lock-env.md(实验环境与依赖先锁定)

→ tier0-core/build-oracle.md(结果正确性判定)

→ tier0-core/reproduce-result.md(结果可复现)

→ tier1-skeleton/statistics-oracle.md(多 seed 结果聚合后,若要下"显著/优于"类结论,过统计关;单次实验产出分布本身不强制,聚合下结论时强制)

→ tier1-skeleton/research-execution-grill.md(已批准 proposal 的实现歧义、实验设计与 pilot→scale 门禁)

## 步骤

1. 读取 `{GRILL_ARTIFACT}` 与 `{HYPOTHESIS_LEDGER}`。普通实现/Phase 0 运行 `{GRILL_VALIDATE_CMD} {GRILL_ARTIFACT} --required-authorization phase0_launch ...`;物质性扩容改为 `--required-authorization scale_launch`。validator 必须重读 external pinned trust policy 与 signed v3 ledger 并 exit `0`;prepared candidate 的 exit `5`、legacy audit `4` 或其他非零结果都不得开跑。
2. 固定实验配置:数据集划分(train/val/**holdout** 隔离)、`{SEED}`、超参、代码 `{GIT_SHA}`(git 干净)。——中间产物复用规则:探索/调参阶段允许复用中间结果(prompt 编码、KV、特征缓存)以省算力;但**任何将写入 HYPOTHESIS_LEDGER 上报的结果,必须来自一次不复用缓存的干净重跑**(与 → tier0-core/reproduce-result.md 步骤 2 一致)。探索省钱与上报可信不冲突,靠"上报前干净重跑"这一刀分开。
3. 跑实验,用 build-oracle 的独立参照判定输出正确性;correctness 不过 → 结果作废,不记指标。
4. 指标算不出(NaN/维度错/缺数据)即**硬失败**,不得填占位或估计值。
5. 随机性:多 `{SEED}` 跑,报分布(均值±方差)而非单点。
6. 结果 + 配置 + 假设结论(证实/证伪)写回 `{HYPOTHESIS_LEDGER}` 与 `{RESULTS_DIR}`(P4);证伪也如实记,不藏。
7. **预算 guard(P4 成本,阻断)**:每个 run 结束读 manifest 的 compute.gpu_hours / compute.total_tokens,累加到批次累计值;累计触及或超过 {BUDGET} 任一上限 → **立即 halt 后续 run 并报告**已消耗 vs 上限,不得静默继续烧。需要超预算续跑 → 回前置重新声明 {BUDGET}(留痕),不得就地默默抬高上限。
8. **假设证伪处置(kill 闭环,P4)**:当本次结果触发假设的 kill criterion(项目 proposal 层定义,如"提升 < X% 即弃")或证伪预注册假设时,不止步于"记个负结果",须走完三步:① 在 HYPOTHESIS_LEDGER 标记该假设为 killed + 触发的判据 + 支撑数据;② 在 docs/DECISIONS.md 记一条方向决策(为何弃、转向何处或止损收尾);③ 若转向,新方向作为新假设回步骤 1 重新预注册。证伪是有效产出,不是失败——但必须留痕成决策,不得"跑砸了就换个方向重跑当无事发生"。

## 门禁

[RUNTIME] 指标算不出即硬失败;correctness 未过不记 speed/quality 分。
[RUNTIME] budget guard:批次累计 compute 超 {BUDGET} 即中止;续跑须显式改 {BUDGET} 并留痕。
[RUNTIME] `{GRILL_ARTIFACT}` 必须匹配当前 proposal hash;实现/Phase 0 的 exact `phase0_launch` 或物质性扩容的 exact `scale_launch` 必须由 schema v3 signed final event 授权且 validator exit `0`;prepared/audit/blocked/过期/缺失均不得启动或扩容。
[REVIEW] 必问:"holdout 有没有泄漏进训练/调参?这次结果是不是单点幸运?"

## 完成判定

- correctness 通过;
- 当前 exact action 的 schema v3 research-execution-grill validator 通过;
- 指标在多 seed 下有分布;
- 结果与配置、假设结论已归档且可复现(经 reproduce-result 校验)。

## 失败处理

遵守 P3:correctness 不过 → 作废该结果,禁止"分还行就先用着";指标算不出 → 硬失败报错,禁止填估计值/占位数;holdout 疑似泄漏 → 判结果不可信并报告,不得"当没看见";实验崩溃 → 报错中止,不静默用上次结果顶替;预算触顶 → halt 并报告,禁止"快跑完了就再烧一点";{BUDGET} 未声明就开跑 → 停在前置报阻塞,不得无预算裸跑(8/3 的 80 元教训:体系当时无任何一条能拦);假设被证伪 → 按步骤 8 记入 HYPOTHESIS_LEDGER(killed)+ DECISIONS.md,不得删记录假装没跑过(灌水红线);触发 kill criterion 却继续投算力硬撬 → 违 P3,halt 并要求先记决策再定去留。

## 产物

一条实验记录:假设 + 配置(`{SEED}`/`{GIT_SHA}`/数据划分)+ correctness 结论 + 指标分布 + 证实/证伪结论,入 `{HYPOTHESIS_LEDGER}`/`{RESULTS_DIR}`;批次算力台账(每 run 的 compute 累计 vs {BUDGET} + 是否触顶 + 续跑决策留痕)。
