# Playbook: 已批准 proposal 的实现与实验

适用于把已经批准的 AI 研究 proposal 忠实地实现出来并跑实验。idea 还没批准时不用这一份。通用规则见 [KERNEL](../KERNEL.md)。

## 1. 冻结 execution contract

开工前写清以下各项，放进实验计划即可：

- 核心 claim 与 primary estimand；
- 方法语义；
- baseline；
- 数据与 split；
- 分析方法；
- 成功和 kill 条件；
- 正式预算。

其中任何一项要实质改变，都要回到人重新确认（re-contract），不能用一个更容易的 claim 替代原任务。

## 2. 方法忠实映射

第一次经验性 run 之前，把 proposal 里的关键语义（公式、loss、mask、更新规则等）逐条映射成：

`proposal 语义 → 代码位置 → 可观察的不变量 → 独立 oracle`

oracle 可以是小规模确定性 fixture、naive 参考实现、独立推导或性质测试。loss 下降、smoke 通过或端到端分数都不能证明方法实现正确。实现者自己写的映射，至少要有一个不依赖该实现路径的检查去尝试证伪。

## 3. 实验设计闭环

正式 pilot 之前检查：

- baseline 与本方法使用相同的数据、信息、预处理，以及可比的训练和调参预算；
- 调参集和最终证据集分离；
- 声称因果机制时，有能区分替代解释的 negative control 或 ablation；
- model judge 或 human judge 的 rubric、顺序和冲突处理与 claim 匹配。

缺哪一项，只阻断依赖它的那个 claim。

## 4. 证据分级

每个 run 启动前声明类别：`diagnostic`、`code_readiness`、`exploratory` 或 `confirmatory`。

- 前两类，以及所有 synthetic、mock 或 smoke 结果，一律 `paper_eligible=false`，不能支持 claim、触发 GO 或进入最终表格。
- 只有协议冻结、使用真实数据、oracle 有效、没有 runtime fallback 的 run 才可以 `paper_eligible=true`。
- 原始 run 不可改写。失败、invalid 和 timeout 也要保留在中间视图里。最终表格只从 eligible 的原始记录确定性生成，不手填数字，不复制论文里的数字。

## 5. 运行

- 实验代码 fail fast（见 KERNEL 第 4 条）。修复后用新的 run ID 重跑，不追认旧 run。
- 每个 run 记录：代码身份、配置、数据、seed、环境、命令、日志和实际消耗的算力。代码身份可以是 clean commit 或内容快照；用 base commit 加 diff 时，要覆盖未跟踪文件和 submodule。
- 只有 claim 需要跨环境可重建时，才锁定环境并独立重建。
- 远程机器信息由项目配置提供，通用规则里不写默认主机。累计资源触及预算就停，扩大规模需要人批准。

## 6. 统计与复现

- 先区分这是有限样本描述、探索性比较，还是确认性推断。只描述冻结 benchmark 上的数字时，不制造 p 值。
- 找出真正独立的重复单位（seed、task 或 item），不要把重复解码或多次 judge 调用当成独立样本。分析时保留配对或嵌套结构。
- 确认性 claim 的 contrast、排除规则、缺失处理和 multiplicity 处理，要在看到结果之前冻结；看过结果后才选定的内容只能算探索性发现。
- 报告 effect、与设计匹配的不确定性和有效 N，并与实际意义上的阈值比较。不显著不等于等效。
- 同环境重跑只能叫 `REPLAYED`；达到预先声明的独立性才叫 `REPRODUCED`。复现外部 baseline 时，自测数字和原论文数字分开列。

## 7. 收尾

- 原 claim 必须落在 `SUPPORTED`、`FALSIFIED`、`NOT_ESTABLISHED` 或 `BLOCKED` 之一。次要发现可以单独列出，但不能替换原结论。
- 负结果也是结果，照实记录并写复盘。
