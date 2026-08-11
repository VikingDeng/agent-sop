# SOP-statistics-oracle: AI 实验的 claim-triggered 统计 Oracle

- **层级**: tier1-skeleton
- **落实纪律**: P1(冻结 estimand、比较与适用范围) P2(统计设计和复算匹配实际 claim) P3(失败、缺失与选择过程不被隐藏) P4(结论可回到 immutable raw runs)
- **绑定骨架**: research
- **通用性档位**: U1（适用于经验性 AI 研究；具体 estimand、抽样结构、分析模型与阈值由项目注入）
- **版本**: v2

## 目标

在 proposal 转化为实验结论时，判断数据究竟支持什么范围的统计 claim。统计 Oracle 先识别数据生成过程、独立 replication unit 和目标 estimand，再选择与 paired、nested 或 crossed 结构匹配的分析；它不指定一个万能检验，也不能把 method-fidelity、实验 eligibility 或运行失败“统计成通过”。

## 触发条件

- 即将提出正式 inferential claim：例如对未观测 seed、task/item、benchmark、model、judge 或运行条件作“优于、等效、非劣、稳定、相关、鲁棒、可泛化”等超出已观察数字本身的结论；
- 即将把比较性统计结论写入 authoritative final table、论文主张或 scale/GO 决策；
- 作者显式要求统计设计、功效/精度、显著性、区间、等效性或结果复核。

以下情况不自动触发全套 inferential gate：`diagnostic`、`code_readiness`、默认 `paper_eligible=false` 的 exploratory run，以及明确限定为“这个冻结有限集合上的观察值”的描述性汇总。它们仍须如实展示 raw points、有效 N、失败与适用范围，但不得换一种措辞暗示总体泛化或确认性结论。

## 前置条件

- 待判断的 claim、目标总体/有限集合、estimand、primary outcome、比较方向与适用范围已明确；等效、非劣或 practical improvement claim 还需项目给出有科学含义的 `{PRACTICAL_MARGIN}`；
- 输入来自 `run-experiment` 保留的 immutable raw run records，能区分 evidence class、`paper_eligible`、配置/代码/数据身份、seed/task/judge 等标识及 `success|failed|invalid|timeout|killed|not_run`；
- correctness、method fidelity、数据/split 和 measurement oracle 已通过或明确标为未决。统计分析不得替这些前置有效性自证；
- 对 confirmatory claim，primary contrast、纳入/排除规则、失败/缺失处理、最大预算或 sequential rule、multiplicity family 与分析方法在接触相应未盲结果前冻结。若结果已经用于选择这些内容，只能标为 exploratory，不能补时间戳追认预注册；
- 有足够标识重建数据生成过程。固定的最小 seed 数不是通用前置条件；证据是否足够取决于 claim、独立单位、效应尺度和所需精度。

## 依赖 SOP

→ tier0-core/build-oracle.md（按可信失败路径建立独立统计检查）。

→ tier0-core/reproduce-result.md（输入与重跑范围可复核）。

→ tier0-core/no-fallback-review.md（禁止为得到有利结论自动换分析路径）。

输入契约遵循 `run-experiment.md` 的 immutable raw runs、evidence class 与 `paper_eligible` 语义；结果展示遵循 [research-evidence-presentation.md](references/research-evidence-presentation.md)。典型禁止模式见 [statistics-redlines.md](references/statistics-redlines.md)，该清单只帮助定位具体失败路径，不是每次分析都要全量执行的固定 gate。

## 步骤

### 1. 先给 claim 分型，不因“有多个数”自动做检验

记录当前结论属于：有限样本描述、exploratory association/comparison，还是 confirmatory inferential claim；写清它要泛化到什么单位和条件。若只报告冻结 benchmark 上的精确聚合值，就把范围限定在该 benchmark，不制造总体 p 值或虚假的 sampling interval。若 claim 包含随机训练、抽样任务、随机 judge 或其他未观测条件，则继续识别对应不确定性。

### 2. 重建数据生成过程和独立 replication unit

对会影响 primary outcome 的来源，说明它是 fixed、sampled 还是 randomized，并标出 nesting/crossing 与共享项。至少按当前 claim 检查：

- training/init/data-order seed 与同一 checkpoint 的重复评测；
- task、item、episode、dataset/benchmark 和它们的 split/group；
- model/backbone、prompt/template、checkpoint 与 tuning selection；
- human/model judge、judge prompt/order、sampling draw 和重复评分；
- 时间、硬件、worker 或系统环境等 block/cluster。

replication unit 是能为目标总体提供独立信息的最小随机化或抽样单位，不是 CSV 的每一行。同一 checkpoint 上重复 decoding、同一 item 的多次 judge call、同一 task 下多个 episode 或同一 seed 导出的多个指标，不能无条件当作新的独立样本。seed 只刻画 seed variation 时，结论不能自动外推到新 task；task 被视为固定完整 benchmark 时，也不能把 item 数伪装成对所有 benchmark 的泛化证据。

### 3. 冻结 estimand、contrast 与决策语义

定义 `{ESTIMAND}`、比较单位、配对键、聚合权重、primary/secondary outcomes、方向、目标误差或区间覆盖语义，以及 practical decision threshold。对 superiority、equivalence、non-inferiority、robustness、failure-rate 或 cost-quality claim 分别写出其判定含义；“没有检出差异”不等于等效，“统计上非零”也不等于有实际价值。

confirmatory 分析必须保留冻结时点和依据。已经看过 outcome 后新增的 contrast、subgroup、metric、checkpoint 或排除规则可作为探索性发现展示，但需完整披露选择过程，并由 fresh holdout/run 或预先允许的独立确认路径支持后续 confirmatory claim。

### 4. 让分析结构匹配设计，而不是套固定检验

- 同一 task/item/seed/block 上同时评测方法时，优先分析同一独立单位内的 contrast，保留配对，不把两组错误地当独立样本；
- seed、task、model、judge 等存在 nested 或 crossed variation 时，分析、cluster/resampling 或 uncertainty propagation 必须反映相关结构，不能用重复行膨胀有效 N；
- training randomness、task sampling、judge disagreement 和 evaluation sampling 是不同不确定性来源。报告哪一层被估计、哪一层被条件化、哪一层因数据不足无法辨识；
- deterministic finite evaluation 可以只给精确描述性 effect；只有确有抽样/随机化或模型化目标总体时才赋予 inferential uncertainty；
- 根据 estimand、设计、样本规模、尾部/有界性、cluster 数和计算预算选择 `{ANALYSIS_METHOD}`。可以使用设计匹配的 randomization、resampling、hierarchical/model-based 或其他方法，但本 SOP 不预设 t-test、非参数检验、bootstrap、Bayesian 或 frequentist 路径中的任何一种。

诊断检查应针对会改变结论的具体失败模式。正态性检验、方差齐性检验或“先检验再自动换方法”不是所有 AI 实验的固定流水线；分析的有效性来自与数据生成过程匹配及必要的 sensitivity/calibration 证据。

### 5. 显式处理失败、缺失、停止与选择

- 在看 outcome 前区分基础设施/measurement invalid 与方法本身的 crash、OOM、timeout、abstain 或无输出；所有正式尝试保留在 run view 和状态计数中，不静默 drop、补 0 或只分析成功者；
- 当 failure 本身属于部署表现时，estimand 应包含 success/failure，或并列报告 failure probability 与 conditional-on-success quality。若结果对 missingness/censoring 假设敏感，报告与 claim 匹配的 sensitivity、bounds 或 `NOT_ESTABLISHED`，不以任意填充值闭环；
- 若运行过程中查看结果并决定继续/停止、换 checkpoint、增减 seed/task 或选择最佳配置，必须把 stopping/selection process 纳入设计。confirmatory 路径使用预先冻结的最大预算与 looks、有效的 sequential/anytime 方案，或使用未参与选择的 fresh confirmation；普通 fixed-N 分析不能在反复窥视后原样解释；
- multiplicity family 根据实际 claim family 冻结，覆盖会被同时宣称或经 outcome 选择的 baseline、metric、dataset、subgroup、checkpoint 和 variant。选择与 `{ERROR_CONTROL}` 匹配的控制/层级策略，或把相关结果明确降为 exploratory；不机械校正所有展示数字，也不把未披露挑选排除在 family 外。

### 6. 以 effect 与匹配的不确定性回答科学问题

报告 primary estimate/contrast 的尺度、方向、有效 N（按 relevant level）、point estimate 和与设计匹配的 uncertainty；适用时同时展示 raw/unit-level distribution。只有 claim 和冻结方案需要假设检验时才报告有效 p 值或 posterior decision quantity，不能强制每项结果凑齐“effect + CI + p”。

将估计量与 `{PRACTICAL_MARGIN}`、成本、风险或领域容忍度比较，分别给出 statistical 与 practical verdict。小而精确但无实际意义的 effect 不能写成重要提升；宽区间或低 power 下的 non-significant 结果是证据不足，不是“相同”。equivalence/non-inferiority 必须由预声明 margin 和相应设计直接支持。

### 7. 建立独立但不过度的统计 Oracle

至少独立核对 headline claim 的数据 lineage、eligible run 集合、配对/cluster 键、状态计数、estimand 实现和关键 contrast。设计 review 应尝试证伪 replication unit、泛化范围、missing/failure、sequential selection 和 multiplicity 假设；计算错误风险显著时，再用可信库、reference calculation、simulation/calibration 或独立实现复算关键量。

复算路径必须独立于待验证错误，而不是换一个调用同一聚合表的包装。两种检验或两个库得出同方向/同“显著性”只说明它们表面一致，不能证明错误的 estimand、配对、独立性或选择过程有效；不一致则必须调查，不能挑有利结果。两个边际 CI 是否重叠也不是方法差异的通用检验，比较性 claim 应直接分析预声明 contrast 及其匹配 uncertainty/decision rule。

### 8. 从 raw evidence 生成可追溯结论

统计报告和 final table 只能从 immutable records 确定性派生。authoritative estimate 只消费符合冻结 protocol 的 eligible runs；正式 `failed|invalid|timeout|killed` 尝试仍进入状态、分母或 sensitivity 的适当位置，不能从事实层删除。分析修复生成带原因和版本的新 derived artifact，保留旧报告；不得修改 raw run、把 `paper_eligible=false` 升级为 true，或让统计显著性覆盖 correctness/method-fidelity 失败。

## 门禁

- replication unit、配对/cluster 结构或泛化总体与实际数据生成过程不符，存在 pseudo-replication；
- outcome-driven 选择 contrast、metric、checkpoint、subgroup、排除、stopping 或分析方法，却仍声称 confirmatory；
- 静默删除/填充 missing、NaN、failed、timeout、abstain，或只保留成功/最佳 seed；
- sequential looks、hyperparameter/model selection 或 claim family 的 multiplicity 足以改变结论但未纳入解释；
- 只凭 p 值宣称有实际价值，以 non-significant 宣称等效，或没有预声明 margin 却声称 non-inferior/equivalent；
- 用边际 CI overlap、两种检验一致或两个库一致替代对 estimand 与设计正确性的验证；
- ineligible/smoke/synthetic/fallback run 进入正式 estimate，或统计分析追认旧 run、弱化原 claim、掩盖 method/oracle failure；
- 主分析失败后自动轮换检验、缺失策略或样本子集，直到得到有利结论。

并非每个探索图、diagnostic run 或描述性表都必须通过上述全部门禁；门禁只阻断其无权支持的 inferential/confirmatory claim。

## 完成判定

若本轮没有 inferential claim：已记录 `not_applicable` 的理由、描述性范围和禁止外推的边界，不制造多余统计 artifact。

若本轮有 inferential claim：

- claim、target population/finite set、estimand、practical margin 与 confirmatory/exploratory 身份明确；
- 数据生成过程、独立 replication unit、paired/nested/crossed 结构和有效 N 可复核；
- failure/missing、sequential stopping、selection 与 multiplicity 的处理和局限明确；
- headline effect、匹配 uncertainty 和 practical/statistical verdict 能回到 eligible raw run IDs；
- 独立 Oracle 覆盖最可能改变结论的设计或计算错误，且没有用表面一致冒充设计有效；
- 最终措辞不超过证据支持范围；原 claim 被标为 `SUPPORTED`、`FALSIFIED`、`NOT_ESTABLISHED` 或 `BLOCKED`，弱发现没有替换它。

## 失败处理

计算或聚合实现错误时，保留旧 derived report，修复代码并从同一 immutable raw records 生成新版本，再运行匹配 Oracle；不得改 raw evidence。若错误来自 replication unit、estimand、unblinded selection、missing/failure 或停止设计，当前 confirmatory claim 保持 `NOT_ESTABLISHED`，已有分析只可按真实身份作为 exploratory/description；需要确认性结论时运行保持原 claim 的 fresh、冻结 protocol。

主分析与 Oracle 不一致时调查数据 lineage、设计和实现，不能选择有利的一条。若精度、独立单位、cluster 数或识别假设不足，报告 effect/范围与不确定性或 `NOT_ESTABLISHED`；不得补伪样本、把重复评分当独立样本、静默换检验或写 runtime fallback code。只有预先声明、仍回答同一 estimand 的等价分析路径可以按原 contract 执行；物质性改变 claim、分析语义、正式数据或预算时进入 re-contract。

## 产物

`{STATS_REPORT}` 或现有报告中的等价结构：applicability 与 claim 身份；target/estimand/contrast/practical margin；数据生成过程、replication unit、配对/层级结构和有效 N；eligible run IDs 与完整状态计数；failure/missing、stopping/selection 和 multiplicity 处理；effect + 匹配 uncertainty；statistical/practical verdict；Oracle 证据；分析代码/配置/版本、局限与原 claim verdict。普通探索或描述性工作只保留与其 claim 强度相称的子集。
