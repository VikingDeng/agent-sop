# SOP-profile-code: 性能画像(先测再优化)

- **层级**: tier0-core
- **落实纪律**: P2(独立测量给证据)+ P4(证据归档可追溯)
- **绑定骨架**: 无(被 build-local-proxy 依赖)
- **通用性档位**: U2(profiler 与指标口径绑定平台/技术栈,必须由项目注入)
- **版本**: v2

## 触发条件

准备做性能优化前、或需要证明"快在哪/瓶颈在哪"时。铁律:**先 profile 再优化,禁止拍脑袋优化**。

## 前置条件

- 有可运行、结果正确的基线(优化对象);优化前正确性应已过 `→ tier0-core/build-oracle.md`;
- 项目声明了 profiler `{PROFILER}`、待测指标 `{METRICS}`、计时口径 `{TIMING_SPEC}`(warmup/repeat/取中位/是否含 H2D-D2H 等)。

## 依赖 SOP

→ tier0-core/build-oracle.md(优化前先证明基线结果正确,再比较性能)。

## 步骤

1. 固定测量条件:同一 build、同一输入、按 `{TIMING_SPEC}` 设定 warmup 与 repeat,消除冷启动/抖动。
2. 用 `{PROFILER}` 采集基线画像(如 CPU: perf;NVIDIA: nsys/ncu;AMD: rocprof;Ascend: 对应 profiler),归档到 `{PROFILE_DIR}/{run_id}/`。
3. 判定瓶颈类型:compute-bound / memory-bound / IO-bound / 串行化——产出 `roofline` 或等价瓶颈分析,决定优化方向。
4. 达标判据先行:若画像显示已吃满资源(高利用率/接近 roofline),即判为"无需继续优化",记录并停止;仅当画像显示明确卡点(CPU 卡点/可缓存复用/可预处理)才继续。
5. 每轮优化后重测,与基线同口径对比,画像与结论一并归档(P4)。

## 门禁

[REVIEW] 必问:"优化方向是画像证据得出的,还是猜的?测量口径和线上/基线一致吗?"
[AUTO] `{PROFILE_DIR}/{run_id}/` 存在且含 profiler 原始产物 + 瓶颈分析。

## 完成判定

- 存在基线画像 + 瓶颈类型判定;
- 每次优化有同口径前后对比且归档;
- 优化决策可回溯到画像证据(二值:证据文件在/不在)。

## 失败处理

遵守 P3:禁止用降级换速度——质量/正确性数与吞吐数必须同一 run 产出,不得"关掉正确性检查跑个快数字";若 profiler 无法运行或数据缺失 → 报错中止,不得凭感觉声称"优化有效";若优化后正确性回退 → 该优化作废,不得"快了就行、正确性回头再说"。

## 产物

`{PROFILE_DIR}/{run_id}/`:profiler 原始产物 + roofline/瓶颈分析 + 关键时序 + 前后对比结论。
