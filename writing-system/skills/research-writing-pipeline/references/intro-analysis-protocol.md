# 论文引言与问题段落的组织范例

本文件是一组**已记录的局部范例**：四篇论文引言的短摘录与信息释放顺序，供重写匹配的论文引言或
问题段落时对照。摘录保持记录时的样子，2026-09-23 维护时未联网、未重新核实来源；论文的结论与整篇质量不由
本文件背书，其中的做法也不是必须套用的模板。

## 四篇论文的短摘录与结构

以下摘录均控制在短语长度，只用于定位组织动作。

### ResNet：先证明“本来有解”，再说明“现有求解器找不到”

来源：[Deep Residual Learning for Image Recognition](https://arxiv.org/abs/1512.03385)，Introduction。

- `Is learning better networks as easy as stacking more layers?`
- `There exists a solution by construction`
- `our current solvers on hand are unable to find solutions`

信息顺序是：领域已经押注更深网络 → 把“深度重要”改写成可检验问题 → 关闭梯度消失这一旧解释 → 给出加深后训练误差升高的反常现象 → 用 identity 构造证明更深模型本来存在不更差的解 → 定位缺口为求解器难以找到该解 → 引入 residual learning。

方法名在前四段没有出现。它第一次出现时已经绑定了明确缺口：问题是 degradation，手段是 residual learning。读者继续读的理由来自一个被证明的矛盾：解存在，求解器却找不到。

### Transformer：从主干的计算机制推出结构瓶颈

来源：[Attention Is All You Need](https://arxiv.org/abs/1706.03762)，Introduction 与 Background。

- `The fundamental constraint of sequential computation, however, remains.`
- `In this work we propose the Transformer`
- `Self-attention, sometimes called intra-attention`

信息顺序是：RNN/LSTM/GRU 是主流 → 隐状态依赖前一位置 → 样本内计算无法并行，长序列时成本更高 → 已有 factorization 与 conditional computation 有帮助，但顺序约束仍在 → attention 能建模远距离依赖，却通常与 recurrent network 配合 → Transformer 占据“只用 attention”的空位。

它没有先定义 self-attention，也没有先列全文目录。术语推迟到读者需要它的位置，贡献句只负责命名已经由前文逼出的设计。

### FlashAttention：把失败归因从 FLOP 转向 IO

来源：[FlashAttention](https://arxiv.org/abs/2205.14135)，Introduction 与 §3。

- `Transformers are slow and memory-hungry on long sequences`
- `tend to ignore overheads from memory access (IO)`
- `a missing principle is making attention algorithms IO-aware`
- `computes exact attention with far fewer memory accesses`

信息顺序是：长序列的二次时间与显存成本 → 稀疏、低秩方法已经降低 FLOP → 实际墙钟收益有限 → 原因是忽略访存 → 提出 IO-aware 原则 → 把目标拆成精确前向归约和反向重计算两个子问题 → 给出算法、复杂度和实验。

它的关键不是多列一个方法，而是重新指定“该优化什么”。“exact”在机制和定理之后得到支撑，不能只靠摘要里的形容词。

### AlphaFold：先交代外部判定标准，再给结果

来源：[Jumper et al., AlphaFold](https://pmc.ncbi.nlm.nih.gov/articles/PMC8371605/)，Main；以及 [DeepMind 官方说明](https://deepmind.google/blog/alphafold-a-solution-to-a-50-year-old-grand-challenge-in-biology/)。

- `existing methods fall far short of atomic accuracy`
- `it is a blind test for the participating methods`
- `recognised as a solution to this grand challenge by the organisers`

正式论文的顺序是：已知结构数量与计算成本的落差 → 问题开放多年 → 现有方法在无同源结构时的条件性缺口 → CASP 盲测协议 → 与次优结果比较 → 泛化复核 → 架构术语。

它把“好”交给外部标准：谁判定、按什么协议、合格线是什么、结果是否在未知样本上成立。数字因此有了意义。

## 四篇论文里常见的组织动作（可选）

四篇引言里反复出现下面这些动作，但四篇并非每篇都做了每一条，也不是必须顺序执行的七步。
按读者与文种取用；手册、教程、设计文档等文种不必套用。

1. **先给读者一个可依赖的事实。** 可以是领域已经押注的变量、计算机制、成本量级、失败现象或外部判定标准；也可以先给读者要用的定义。
2. **把事实写成问题。** 问题由前文推出，不凭空宣布“仍有挑战”。
3. **先处理最可能的旧解释。** ResNet 排除梯度消失和过拟合；FlashAttention 排除“只要减少 FLOP 就会加速”；Transformer 承认已有优化后指出顺序约束仍在。
4. **把缺口落到对象和机制。** 是求解器找不到解、顺序依赖无法消除、访存成为瓶颈，还是评价协议缺失。
5. **术语与需求的位置。** 在这几篇论证型引言里，方法名第一次出现时同时说明它解决的对象或约束；参考规范型文本可以先给定义，再讲用途。
6. **方法或分析之后紧跟可核对物。** 可以是构造证明、复杂度、盲测协议、同构基线或明确实验主张。
7. **章节组织从前文问题推出。** 这些引言没有提前宣告目录；读者需要导航时（长文档、手册、路线图），导航可以出现，位置按读者何时需要定位来定。

## 条件化示例：把这套动作用到综述的大段落

下面是一个**流程示例**，只在综述需要按问题链重排大段落时参考。它不是文种要求，不要求每段都以
一个问题收尾，也不涉及本轮未核查的具体技术判断。

1. **列出读者已有的事实**：只写能被引用、公式、图或现有实验支撑的内容。
2. **找事实之间的断口**：搜索对象扩大而制度未变、分数上升但归因不清一类可检验的差异；
   一段只取一个断口，不同时放入定义、历史、分类与展望。
3. **检查旧解释是否已被材料排除**：没有实验、构造、外部协议或机制分析时，不写“问题在于 X”，
   把句子收窄到材料支持的范围。
4. **让代表工作承担判断**：一篇工作出场时说明它让读者多知道什么；名称不单独承担时间线功能。
5. **需要区分时再引入形式化**：先让读者看到普通反馈环的含义，再写

   $$A_{t+1}=I_t(A_t,E_t).$$

   当读者需要区分“改进过程本身是否变化”时，再写

   $$I_{t+1}=J(I_t,A_t,H_t).$$

   两条公式只作概念示意，不是经验证据，也不用它们宣布统一框架。
6. **章节顺序回答前文问题**：对象如何扩展、哪些状态跨代保留、怎样验证、哪些瓶颈限制外推；
   读者需要定位时，导航可以出现。

## 抽查问题（按适用范围取用，不逐条强答）

1. 第一段结束时，读者掌握了哪个具体事实？
2. 代表工作删掉后，段落是否还剩一个可判断的命题？
3. 术语首次出现时，读者是否已经知道它要解决什么？（先给定义的参考型文本不适用）
4. 每个限制是否绑定了对象、条件和证据，而不是泛称“挑战”？
5. 删除“本文将……”“本章主要……”后，论证是否仍然成立？

这些是抽查线索，不是每段必须通过的检查表，也不要求每段都留下一个由下一段回答的问题。
已经清楚的段落可以不改，只有定位到具体阅读障碍时，才回到材料顺序处理。
