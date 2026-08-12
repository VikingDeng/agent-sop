# SOP-reproduce-result: 复现一个结果

- **层级**: tier0-core
- **落实纪律**: P1(先定义复现 claim) P2(独立性与 oracle 匹配) P3(差异诚实) P4(来源、配置与结果可追溯)
- **绑定骨架**: 无（被 run-experiment、ops-deploy 依赖）
- **通用性档位**: U1（复现机制通用；独立性轴、容差与载体由项目注入）
- **版本**: v2

## 触发条件

- 需要确认实验指标、构建产物、部署行为或报告数据可再次得到，而非一次性偶然；
- 需要跨进程、缓存、机器、环境、实现或 evaluator 验证某个结果；
- 需要确认外部 baseline 在本项目条件下的自测结果，避免把论文或榜单数字冒充本地复现。

不是每个 diagnostic、code-readiness fixture 或低成本 exploratory run 都要独立复现。只有重复性或共享错误路径会改变当前决定、交付或 claim 时才触发本 SOP；否则保存足够的执行 identity 即可。

## 前置条件

- 目标结果、比较对象、可接受差异 `{TOLERANCE}` 或结构判据、以及复现范围已经写清；
- 已声明本次要证明的是 same-environment replay、fresh-process/workspace replay、cache-isolated replay、cross-environment reproduction、independent implementation/evaluator，还是外部 baseline reproduction；
- 原结果的实际 source、输入、配置、数据、随机性和相关运行环境可识别。source identity 可以是 clean commit，也可以是不可变 content-addressed snapshot/archive。若使用 `base SHA + delta`，必须覆盖 staged、unstaged、execution-relevant untracked、submodule/LFS 与仓库外代码身份，并以重建后的 content-tree hash 对拍；dirty tree 本身不是失败。

## 依赖 SOP

→ tier0-core/lock-env.md（只有环境等价性会影响当前结果，或声称跨环境/可重建复现时）。

## 步骤

1. **冻结复现契约。** 写明原结果、复现类型、独立性轴、比较单位、容差/判据、允许共享的工件，以及哪些差异会改变 verdict。普通 rerun 只能支持 replay；没有达到预声明的独立性，不得称为 independent reproduction。
2. **定位可信共享错误路径。** 根据风险选择需要打断的相关性：fresh process/workspace、cache-isolated build、不同 host/backend/environment、独立实现/evaluator 或独立数据解析。缓存若属于冻结方法、身份可核验且不会掩盖目标 failure mode，可以复用；只有 stale cache、中间产物污染、旧 binary 或训练状态可能改变结论时才清理相关缓存或重建。禁止机械禁用一切缓存。
3. **保存精确执行 identity。** 记录实际执行的 source、配置、输入/数据、seed 或随机化规则、相关环境和 oracle。clean Git 是一种充分载体但不是通用要求；使用 dirty tree 时优先保存 content-addressed snapshot/archive。若使用 base+delta，按前置条件覆盖所有 execution-relevant 内容并对拍重建后的 content-tree hash；普通 `git diff` 不包含全部未跟踪/外部身份，不能单独充当精确快照，也不能只记录 base SHA 冒充实际代码。
4. **按契约重跑并比较。** 数值、结构、状态与失败语义使用匹配的 oracle；保留原结果与新结果、差异和运行失败。不能因为不一致就扩大容差、换指标、改 split 或选择性丢弃复现 run。
5. **让重复次数匹配数据生成过程。** 随机性结果按 estimand、独立单位、pairing/nesting、方差和所需精度决定 repetitions/seeds；不规定通用 `{N_SEEDS}`，也不用一次幸运结果声称稳定。确定性结果若一次独立验证已排除目标共享错误，可停止机械重复。
6. **复现外部 baseline 时恢复可比条件。** 锁定论文/官方 repo/权重的精确来源；对齐数据与 split、实现版本、模型与 prompt/template、超参、训练/评测和 tuning budget、信息可见性及 evaluator。把本项目自测数与原报告数分列；对不一致项和算力限制显式说明。复不出原数时报告差距，不得直接引用原文数字或使用失配的弱 baseline 抬高相对提升。
7. **把结果用于决定。** same-environment 或未打断冻结共享错误路径的成功重跑输出 `REPLAYED`；只有达到预声明 independence level 的成功验证才输出 `REPRODUCED`。其余输出 `DIVERGED`、`NOT_ESTABLISHED` 或 `BLOCKED`，并标明适用范围。完成决定所需的独立性后停止；不要为流程完整感继续无信息量重跑。

## 门禁

- `[BLOCK]` 实际 source、输入、配置或结果不可恢复，却声称复现了指定结果；
- `[BLOCK]` 声称 cache-isolated、cross-environment 或 independent reproduction，但复用关系会掩盖预声明 failure mode；
- `[BLOCK]` baseline 的版本、数据、评测口径、信息或 tuning budget 失配，却声称公平复现或沿用原报告数；
- `[SIGNAL]` 当前只有 same-environment replay 时，限制复现措辞和外推范围，不否定其真实运行事实；
- `[HUMAN]` 新外部凭据、受控数据、生产动作、不可逆操作或 material/unbounded 资源按 Supervisor 授权边界处理。

clean Git、全新环境、清空所有缓存、固定 `{N_SEEDS}` 和完整外部 baseline 重跑都不是通用门禁；它们只在对应 failure path、claim 或授权范围触发时成立。

## 完成判定

- 原结果与新结果、复现契约、实际执行 identity、比较方法和差异可复核；
- verdict 与真实达到的 replay/reproduction 独立性一致，没有以较弱重跑冒充较强复现；
- repetitions 与当前随机过程及措辞相称，或 `not_applicable` 理由可复核；
- baseline 场景的来源、可比条件、自测数、原报告数与差异均已记录；
- divergence、失败和限制原样保留，没有事后放宽判据或 cherry-pick。

## 失败处理

结果超出冻结判据时记为 `DIVERGED` 并检查 source、环境、数据、随机性、缓存、实现和 evaluator 的具体差异；信息不足时为 `NOT_ESTABLISHED`，运行或权限不可达时为 `BLOCKED`。可以在新 identity 下修复同一 failure path 并 fresh rerun，但不得编辑旧 evidence、自动切换方法/backend/data/metric 或降低原 claim。某个独立性轴暂不可达，只降低 reproduction status 和相应 claim，不把与它无关的真实工作全部判失败。

## 产物

一份与当前 claim 相称的复现记录：目标与判据、replay/reproduction 类型、实际 source/environment/input/config/randomness identity、允许共享与已隔离的工件、原/新结果、差异、independence level、`REPLAYED|REPRODUCED|DIVERGED|NOT_ESTABLISHED|BLOCKED` verdict，以及 baseline 场景的来源与可比性表。独立环境脚本、cache-clean 报告或多 seed 分布均为条件产物，不创建空壳。
