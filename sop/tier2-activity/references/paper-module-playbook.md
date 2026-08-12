# 论文四模块套路手册(scientific-paper SOP 边车 · 中英双语)

> 本手册是 scientific-paper.md 的 references 边车。SOP 正文只留骨架,穷举型套路下沉到此。
> 来源:Peyton Jones / Swales CARS / McEnerney / 沈向洋十问 / ML 实验可复现标准。取判据不搬原文。

## §1 Introduction 四段式(CARS × Peyton Jones × McEnerney)

四个 move,顺序不可乱:
1. **立地盘(Establish territory)**:1–2 句说清问题重要,直接切入,不铺时代背景。
2. **造空缺(Establish niche)**:指出现有工作的 gap —— 缺什么、错在哪、没覆盖什么。gap 是全篇支点。
3. **问题陈述 + 具体例子**:用一个具体例子把问题讲活(Peyton Jones:don't describe abstractly, use an example)。
4. **贡献 bullet 列表**:结尾列 contributions,每条(a)可证伪、(b)指向正文某节 (§N)、(c)写"读者能拿走什么"而非"我做了什么"(McEnerney: value not knowledge)。

判据:引言读完,读者能答出"gap 是什么、你的贡献凭什么填这个 gap"。答不出 → 引言失败。

中英差异:
- 英:禁 "In recent years / with the rapid development of / it is worth noting"(= PROSE Tier1 英文版)。时态:领域共识用一般现在时。
- 中:禁"随着……的发展/近年来/众所周知"。Move 1 直接切入,不写背景综述。

## §2 Related Work 组织法(主题聚类,非流水账)

- **反模式**:"[1] did X. [2] did Y."(逐篇罗列,读者看不出你的立场)。
- **套路**:漏斗式 + 按 2–4 个 theme 分组。每 theme 先概括"这一脉络共同做了什么、共同局限",再收一句"与本文差异"。
- **每簇必回指本文**:"Unlike these, we ..."。related work 的目的是给自己的 novelty 定坐标,不是证明读得多。
- 判据:每个引用簇能答"他们的共同缺口是什么、我凭什么不同"。答不出 = 流水账。

中英差异:
- 英:领域共识用现在完成时,具体方法用一般现在时。
- 中:避免"XX等人提出了……;YY等人提出了……"排比;用归类动词("这一类方法普遍……")。

## §3 方法段(Method):可复现是硬标准

1. **先总后分**:开头给方法全貌(overview 图/段),再拆模块。Present idea first, details later.
2. **符号一次定义、全篇一致**(接 PROSE §5 术语一次定名)。
3. **每个设计选择给理由**:写"为什么是 X 不是 Y",否则被当随意选择攻击。
4. **可复现身份**（接 reproduce-result）：从实际 claim 和 artifact 反推 outcome-relevant 细节，例如数据来源/规模/预处理、模型与超参、随机性、硬件/backend、评测协议和实际 source/environment identity。缺少会改变目标 claim 或阻止复核的关键细节才阻断；确定性、硬件无关或不适用的字段明确记 `N/A`，不机械补齐清单。

判据:一个独立研究者能否照方法段复现,无需联系作者。

## §4 实验(Experiments):claim-driven,非 result-dumping

1. **先声明本节验证哪几条 claim**,每个实验对应一条 claim(回指 SOP 步骤 1 的贡献列表)。
2. **主结果表打头**(比 baseline 好)+ **消融紧随**(每个组件都有用、好在哪)。
3. **每图表配一句"说明了什么"**;caption 写"展示什么",正文写"意味着什么",不重复(PROSE §5)。
4. **公平性交代**(接 contamination-check):baseline 同条件?调过参?同评测集?无数据泄漏?
5. **主动报负面结果/失败 case**(P3):审稿人最信这个。

判据:每个表/图能回指它验证的那条 claim;没有 claim 认领的图表应删。

## §5 Abstract 四句式 + Conclusion

摘要四句(可扩到 4–6 句):
1. 问题与其重要性(一句);
2. 现有方法的 gap(一句);
3. 我们做了什么 + 核心方法(一到两句);
4. 关键结果(带数字)+ 影响(一句)。

Conclusion:回答引言提出的问题,总结贡献是否兑现,可留未来工作;**禁止**冒出正文没铺垫的新论点(PROSE §2.3 首尾闭合)。

## §6 写作顺序(物理约束防超证据)

成文顺序:Method → Experiments → Related Work → Introduction → Abstract → Conclusion。
理由:先把证据(方法+实验)写实,再回头写"宣称"(引言贡献/摘要),从结构上杜绝"开头宣称的贡献超过正文兑现的"。这是 PROSE §2.3 的论文级落地。
