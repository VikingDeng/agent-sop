# SOP-build-oracle: 建立可信验证 oracle

- **层级**: tier0-core
- **落实纪律**: P2(匹配 claim 的独立证据) P3(证据不足时诚实限界)
- **绑定骨架**: 无(被开发、科研、竞赛与写作 SOP 按需依赖)
- **通用性档位**: U0(普适；具体 evaluator/checker/证据由项目注入)
- **版本**: v3

## 触发条件

一个重要的 correctness、score、行为或事实 claim 不能仅靠产物/实现者自述成立，或已有 evaluator 与被测对象可能共享同一失败路径。

## 前置条件

- 已把待验证 claim 写成可观察结果，并知道 claim 不成立时至少一种可信表现；
- 能取得官方 evaluator、性质/证明、参考实现、黄金样本、独立来源、评委 rubric 或其他证据中的至少一种；若都没有，允许先明确验证上限而不是伪造 oracle。

## 依赖 SOP

无(基础能力,被上层依赖)。

## 步骤

1. 把“正确”或“成立”限定到实际 claim：输入/条件、允许误差、输出/行为、资源边界和不声称什么。评分、排序、rubric 与统计 claim 不强行压成二值 correctness。
2. 选择最便宜且能区分主要失败的证据，通常优先使用比赛/项目的**官方 checker、evaluator、verifier 或协议**；再按问题选择解析性质/证明、不同实现路径的 reference、黄金样本、differential/metamorphic/property test、独立信源或有明确 rubric 的人类判断。官方 hidden judge 是最终 verdict 来源，本地近似只能标为 surrogate。
3. 检查失败路径独立性，而不是只检查文件位置。若复用相同公式、解析器、数据处理或实现核心会共同出错，则改用不同路径或互补证据；只有这种共享错误风险真实存在时才物理隔离 oracle 代码/数据，不强制固定 `src/oracle/` 目录。
4. 按输入合同与已识别 failure mode 选择边界、反例、异常路径和资源限制。空输入、极端 shape、数值稳定性、timeout、协议顺序等只在适用时启用，不复制通用边界清单制造虚假覆盖。
5. 运行 oracle 并保留能支持结论的最小证据。输出可以是 `pass/fail`、score、区间/分布、rubric coverage 或 `[UNCERTAIN]`；必须说明它能支持到哪一层 claim，不能把 surrogate score 写成官方 verdict。
6. 对高影响或弱 oracle 做一次 sanity/control：已知好样本应通过、已知坏样本应失败，或用第二种失败路径不同的证据交叉检查。简单可逆任务有一个直接可信 oracle 即可停止。
7. 对 public API/兼容 contract，Oracle 要覆盖调用方可见语义而不只覆盖所选实现：至少区分默认行为与显式 opt-in，并按真实 failure path 检查 success/error cleanup、外部资源状态保持和平台限制。若存在另一个同样合理的 contract，先用 repository/user evidence 比较两者；独立 review 应能挑战 contract 选择，而不只是寻找当前实现里的 bug。没有这种歧义或失败路径时不制造行为矩阵。

## 门禁

- `[BLOCK]` 关键 claim 仅由被测实现、实现者自述或共享同一核心错误路径的检查自证；
- `[BLOCK]` oracle 已失败/报错，却仍把对象写成通过；
- `[SIGNAL]` 只有近似代理、样本覆盖或主观 rubric 时，收窄结论并暴露不确定性，不因缺少完美 oracle 阻断无关的安全工作；
- `[REVIEW]` 只有 claim 影响大、oracle 弱/共享、或独立判断能发现具体失败模式时才增加第二视角。

## 完成判定

- claim 与 oracle/evidence 的对应关系明确，证据能区分至少一个主要失败路径；
- oracle 的独立性和覆盖强度与失败代价相称，已知限制没有被包装成通过；
- 一次真实运行或检查产生可查结果；需要官方 verdict 时，本地证据未冒充官方结果。

## 失败处理

找不到足够独立的参照时，把相应结论标为 `[UNCERTAIN]`、说明还能支持的较窄 claim，并继续不依赖该结论的安全工作；不得用“看起来对”补位。oracle 自身失败时保留错误并修复或换用质量等价证据，再按未改变的 claim 验收。官方 evaluator 与本地证据冲突时，以适用官方规则下的结果为准，诊断共享实现、环境和代理 gap，而不是挑选更好看的数字。

## 产物

claim、所选 oracle/evidence、一次实际结果及其验证边界。载体可以是测试、官方 receipt、benchmark 输出、review 结论、issue/PR 或现有报告；只有生命周期需要时才创建独立 oracle 目录、完整用例清单或长期台账。
