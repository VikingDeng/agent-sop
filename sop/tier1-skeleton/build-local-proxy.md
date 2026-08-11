# SOP-build-local-proxy: 建立本地评测代理

- **层级**: tier1-skeleton
- **落实纪律**: P2(用校准过的本地证据降低官方反馈不确定性) P3(不把代理冒充官方 verdict)
- **绑定骨架**: competition
- **通用性档位**: U2(官方口径、数据切分、硬件与 proxy 实现由比赛注入)
- **版本**: v2

## 触发条件

官方评测不能本地运行，或线上反馈慢、昂贵、噪声大、隐藏/受提交次数限制，且一个本地 surrogate、holdout 或模拟 judge 能显著改善方案选择。

官方 evaluator/checker/harness 已能本地运行时直接复用；只有格式/pipeline 风险且一次获授权的廉价 baseline 提交信息量更高时，可以先做官方 smoke。`local proxy first` 不是无条件门禁。

## 前置条件

- 已知官方 metric/verdict/rubric、关键资源与反馈限制；不知道的部分被明确列为 proxy gap；
- 有至少一个能本地观察的信号，例如参考答案、公开训练数据、官方样例/runner、可控硬件测量、协议模拟或 rubric 对应的真实产品证据；
- 需要判 correctness 时按 `→ tier0-core/build-oracle.md` 选择匹配证据，不把 proxy 自身当独立正确性证明。

## 依赖 SOP

→ tier0-core/build-oracle.md(关键 correctness/claim 需要与代理失败路径不同的证据)

## 步骤

1. 先判断是否真的需要“代理”：按信息保真度优先使用官方本地 evaluator、官方 checker/runner、独立 exact evaluator，再到近似 surrogate/holdout；若只需一次便宜的官方 pipeline smoke，不先搭完整本地榜。
2. 冻结代理要预测的决策，而不是追求复制整个平台。算法题可用小规模 brute/differential；interactive 可用 local judge/协议故障；数据赛用 train/validation/final holdout；性能赛用同 workload measurement；rubric 黑客松用真实运行、集成、用户路径和 demo evidence，而不是伪造“评委分”。
3. 隔离探索反馈与最终证据。经验性调参不得反复窥探 final holdout；public leaderboard probe、隐藏 evaluator query 或人工评审反馈消耗稀缺预算时，按 `run-competition` 的外部动作包络记录并保留 reserve。
4. 用最少的官方反馈校准方向、尺度和已知差异。记录会改变决策的 gap：硬件/数据分布、public-private 差异、容器/网络、随机性、交互协议、人工 rubric 或平台构建过程；不要求每次都生成百分比 gap。
5. 检查代理是否有预测价值：它至少能拒绝已知坏候选、保持候选排序的有用部分，或稳定暴露目标 failure mode。若与官方结果持续背离，修复、降权或移除代理，不因已投入成本继续维护。
6. 达到当前候选选择所需置信度即停止。proxy 是减少昂贵反馈的工具，不是必须无限本地运行的第二排行榜，也不负责决定外部提交授权。

## 门禁

- `[BLOCK]` 把近似 proxy、public LB 或被反复调参的 holdout 写成 private/final/official verdict；
- `[BLOCK]` correctness/合法性已失败，却只报告 proxy speed/score；
- `[SIGNAL]` local↔official gap 超过当前决策容忍度时，降低代理权重并优先校准，不盲目增加本地优化；
- `[REVIEW]` 只有泄漏、共享 evaluator、口径错位、硬件噪声或协议模拟存在具体失败模式时复核。

## 完成判定

- 代理真实运行过，并能支持一个明确的候选选择/淘汰决定；
- 官方口径、代理口径、已知 gap 与不能支持的 claim 已说明；
- 经验性任务的探索集与 final holdout/官方反馈边界未被破坏；
- 代理成本低于它节省的官方反馈或错误提交成本。若做不到，诚实选择不用代理也可完成本 SOP 的决策。

## 失败处理

本地无法复刻线上环境时，把代理收窄到能验证的性质或直接依赖剩余授权的官方反馈，不虚构一致性。代理与线上冲突时保留两边证据，检查工件、环境、metric、数据和平台 pipeline；未解释前不挑更好看的分数。holdout 泄漏后停止把它当 final evidence，并用尚未触碰的新 evidence 验证受影响结论；没有 fresh evidence 时报告限制。

## 产物

可运行的最小 evaluator/surrogate/holdout 或明确的“不建代理”决定，以及其口径、一次实际结果和关键 gap。可放在项目原生测试/benchmark/issue 中；只有长期反复提交或跨 session 时才维护 `bench/`、`LEADERBOARD_PROXY.md` 或完整 gap 历史。
