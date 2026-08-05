# SOP-run-experiment: 运行一次可信实验

- **层级**: tier1-skeleton
- **落实纪律**: P1(假设先注册)+ P2(独立 oracle 判正确)+ P4(结果绑配置可追溯)
- **绑定骨架**: research
- **通用性档位**: U2(指标/数据集/模型绑具体研究,需项目注入)
- **版本**: v1

## 触发条件

research 骨架项目中,需要跑一次实验产出用于决策/汇报的结果时。

## 前置条件

- 假设已预注册到 `{HYPOTHESIS_LEDGER}`(要验证什么、预期方向、成功判据),防事后编故事;
- 环境已按 `→ tier0-core/lock-env.md` 锁定;
- 正确性 oracle 已按 `→ tier0-core/build-oracle.md` 就位;
- **执行位置已定**:实验在远程服务器执行(科研骨架 §4.6,本机禁止跑实验),契约阶段已确认执行机或至少已记录资源需求。

## 依赖 SOP

→ tier0-core/build-oracle.md(结果正确性判定)
→ tier0-core/reproduce-result.md(结果可复现)

## 步骤

1. 从 `{HYPOTHESIS_LEDGER}` 取本次要验证的假设与成功判据(先有判据,后跑实验)。
2. 固定实验配置:数据集划分(train/val/**holdout** 隔离)、`{SEED}`、超参、代码 `{GIT_SHA}`(git 干净)。
3. 跑实验,用 build-oracle 的独立参照判定输出正确性;correctness 不过 → 结果作废,不记指标。
4. 指标算不出(NaN/维度错/缺数据)即**硬失败**,不得填占位或估计值。
5. 随机性:多 `{SEED}` 跑,报分布(均值±方差)而非单点。
6. 结果 + 配置 + 假设结论(证实/证伪)写回 `{HYPOTHESIS_LEDGER}` 与 `{RESULTS_DIR}`(P4);证伪也如实记,不藏。

## 门禁

[RUNTIME] 指标算不出即硬失败;correctness 未过不记 speed/quality 分。
[REVIEW] 必问:"holdout 有没有泄漏进训练/调参?这次结果是不是单点幸运?"

## 完成判定

- correctness 通过;
- 指标在多 seed 下有分布;
- 结果与配置、假设结论已归档且可复现(经 reproduce-result 校验)。

## 失败处理

遵守 P3:correctness 不过 → 作废该结果,禁止"分还行就先用着";指标算不出 → 硬失败报错,禁止填估计值/占位数;holdout 疑似泄漏 → 判结果不可信并报告,不得"当没看见";实验崩溃 → 报错中止,不静默用上次结果顶替。

## 产物

一条实验记录:假设 + 配置(`{SEED}`/`{GIT_SHA}`/数据划分)+ correctness 结论 + 指标分布 + 证实/证伪结论,入 `{HYPOTHESIS_LEDGER}`/`{RESULTS_DIR}`。
