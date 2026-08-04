# SOP-build-local-proxy: 搭建本地榜单代理

- **层级**: tier1-skeleton
- **落实纪律**: P2(本地代理即独立可无限跑的客观分)
- **绑定骨架**: competition
- **通用性档位**: U2(计时口径/指标绑具体赛,需项目注入)
- **版本**: v1

## 触发条件

competition 骨架中,线上榜是慢反馈/有次数限制的黑箱,需要把线上分复刻成本地可无限跑的客观分时。

## 前置条件

- 已理解官方判分口径 `{TIMING_SPEC}`(warmup/repeat/中位或均值/是否含 H2D-D2H)与待测指标 `{METRICS}`;
- correctness gate 已就位(`→ tier0-core/build-oracle.md`);
- 需要性能画像支撑时,profiler 就位(`→ tier0-core/profile-code.md`)。

## 依赖 SOP

→ tier0-core/build-oracle.md(correctness 是门,先于 speed)
→ tier0-core/profile-code.md(speed 优化需画像证据)

## 步骤

1. 建 correctness gate(门):独立 oracle 对拍,覆盖边界/极端 shape/数值稳定性;返回二值,fail 即作废。
2. 建 speed/多目标测量(分):严格按 `{TIMING_SPEC}` 复刻线上口径;系统赛输出 Pareto 点(latency×throughput×mem×accuracy)而非单值。
3. 测量与正确性同源:同一 build、同一输入。
4. 榜单预测赛:强制 local holdout,本地代理分要能预测 private LB 趋势;probe public LB 次数进台账。
5. 写 `LEADERBOARD_PROXY.md`:口径对齐说明 + 硬件差异 + 历次本地 vs 线上 gap。gap 收敛度 = 代理可信度。

## 门禁

[AUTO] correctness=pass 才允许记 speed 分。
[REVIEW] 必问:"本地口径和线上一致吗?gap 稳定吗?holdout 会不会被反复 probe 过拟合?"

## 完成判定

- correctness gate + speed 测量可无限本地跑;
- `LEADERBOARD_PROXY.md` 有口径对齐与 gap 记录(二值:文件+一次跑通)。

## 失败处理

遵守 P3:correctness 未过禁记 speed;测量口径与线上不符 → 报告代理失真,不得"本地数字好看就当准";若本地无法复刻线上口径(缺硬件/黑箱)→ 如实标注 gap 不可控,不得假装代理可信;禁止用降级/关正确性换本地快数字(质量数与吞吐同一 run)。

## 产物

`bench/`:correctness/(oracle 对拍)+ speed/(计时)+ (预测赛)holdout/ + `LEADERBOARD_PROXY.md`。
