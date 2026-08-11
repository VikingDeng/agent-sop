# SOP-profile-code: 性能测量与按需画像

- **层级**: tier0-core
- **落实纪律**: P2(测量支持性能 claim) P4(关键证据可追溯)
- **绑定骨架**: 无(开发、竞赛与科研按性能风险调用)
- **通用性档位**: U2(指标、工作负载、平台工具与噪声阈值由项目注入)
- **版本**: v3

## 触发条件

性能/资源是验收或得分的一部分，且需要建立可信基线；或现有 benchmark 只能说明“变快/变慢”，尚不能区分下一步的瓶颈、回归来源或因果机制。

不是所有优化前都必须运行 heavyweight profiler。复杂度显然错误、重复工作可直接消除、或稳定 benchmark 已足以判定一个小改动时，可先做最小实现再同口径测量；只有剩余不确定性值得工具成本时才升级画像。

## 前置条件

- 有可运行候选与可比较 workload；会影响结果语义的正确性/质量已用 `→ tier0-core/build-oracle.md` 建立相称证据；
- 项目给出 `{METRICS}`、`{WORKLOAD}`、`{TIMING_SPEC}`、允许误差/噪声和适用平台；工具 `{PROFILER}` 可以暂未选定。

## 依赖 SOP

→ tier0-core/build-oracle.md(性能数字只属于同一语义正确的候选)。

## 步骤

1. 先固定可比较的 baseline、workload、build/runtime 条件和 `{TIMING_SPEC}`；按风险处理 warmup、repeat、同步、缓存、H2D/D2H、并发与硬件噪声，记录真正会改变结论的条件。
2. 用最轻的测量回答当前问题：稳定计时/计数器可判定收益时不加载 profiler；需要定位系统时序、kernel、IO、内存或资源争用时，再选平台原生工具，例如 system trace、`perf`、nsys/ncu、rocprof 或 Ascend profiler。
3. 只提出证据可支持的瓶颈结论。compute/memory/IO/serialization、launch overhead、roofline 或关键 timeline 不是固定输出；它们只在相应数据和优化决定需要时生成。
4. 实施一个与当前证据对应的变化，用同一候选、workload 和计量口径比较。若改变了正确性、精度、模型、输入、编译选项或评分路径，则同步复验相关质量，不能把语义变化写成纯性能收益。
5. 后续每轮都运行能判定回归/收益的 benchmark；只有瓶颈假设改变、结果异常、机制 claim 重要或最终高价值提交需要时才重新 profile。一次可信原始记录可支持多个相同条件下的决定，不按轮次复制档案。
6. 当收益落入噪声、优化方向无具体证据、资源已接近适用上限或预期收益低于验证成本时停止；“还能再 profile”不是继续理由。

## 门禁

- `[BLOCK]` 比较使用不同语义候选、不同评分路径或未披露的测量条件，却宣称净性能收益；
- `[BLOCK]` 正确性/质量已回退，仍只报告速度；
- `[SIGNAL]` profiler 不可用时，可以用稳定 benchmark、计数器或替代平台证据继续判定结果，但不得声称未被证据支持的瓶颈/机制；
- `[REVIEW]` 只有测量口径、噪声、硬件差异、评分路径或高价值机制 claim 存在具体失败模式时复核。

## 完成判定

- 有同口径 baseline 与候选结果，证据足以支持实际的性能/资源 claim；
- 若声称具体瓶颈或机制，存在能区分它与主要替代解释的测量；若只声称 observed delta，不强制 profiler/roofline；
- 正确性/质量和性能属于同一候选，噪声与平台限制被如实界定；
- 关键结果与条件可查，但没有为每轮制造重复原始档案。

## 失败处理

测量不稳定时先定位同步、环境、缓存、采样和 workload 问题；无法控制则报告区间/不确定性，不挑最好一次。profiler 失败不等于优化任务整体失败：保留错误，改用能保持 claim 强度的最低成本证据；若替代证据只能证明 observed delta，就收窄结论。优化导致 correctness/quality 回退时作废该收益或按比赛明确的多目标规则重新评价，不得静默降级。

## 产物

baseline、候选、workload/计量口径、比较结果和实际结论。profiler 原始记录、timeline、roofline、硬件快照与长期 profile 目录均为 claim/risk 触发的条件产物，不要求固定 `{PROFILE_DIR}/{run_id}` 结构。
