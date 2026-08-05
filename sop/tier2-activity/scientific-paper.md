# SOP-scientific-paper: 科研论文写作

- **层级**: tier2-activity
- **落实纪律**: P1(贡献即契约,先定 claim)/ P2(claim↔evidence 独立审稿关)/ P3(不超证据、不藏失败)/ P4(每个结论可回指证据)
- **绑定骨架**: research(研究骨架产出论文时调用)
- **通用性档位**: U1(论文结构套路跨领域通用;领域内容与语言以 {参数} 注入)
- **版本**: v1

## 触发条件

`[显式]` 作者要求"写论文 / 写某一章(intro/related work/method/experiments) / 改论文结构"。
`[信号自触发]` research 骨架实验完成、进入成文阶段时进入本 SOP —— 进入即先走"确认要 claim 什么",不得直接成文。

## 前置条件

- 研究工作已有可写的结果(方法定型、实验有数据);
- 作者已给出核心 claim(本文主张什么)与目标语言(中/英);未给 claim → 停,先问,不得 agent 自行脑补(PROSE §0)。
- 已读边车套路手册:references/paper-module-playbook.md。

## 依赖 SOP

→ tier0-core/build-oracle.md(方法/实验正确性:claim 的证据是否被独立验证)。
→ tier1-skeleton/reproduce-result.md(方法段可复现性下界)。
→ tier1-skeleton/contamination-check.md(实验数据无污染,baseline 公平)。
→ PROSE_STANDARD.md(全文语言/风格/AI 味,走风格关)。

## 步骤

> 分段节奏(Checkpoint 节奏):步骤 1 是方向 checkpoint,必须先与作者确认 claim 与贡献列表再动笔;确认后步骤 2–6 按边车套路自动成文;末尾走门禁三关汇总。**引言/摘要/结论最后写**(PROSE §2.3),先把方法与实验写实。

1. **定 claim 与贡献(契约先行,P1)**:与作者确认"本文主张哪几条 claim、每条贡献读者能拿走什么(value-to-reader,非 knowledge-dump)"。写成贡献 bullet 列表,每条**可证伪、可指向正文某节**。此列表即本文契约,后续所有段落对照它。**Checkpoint**:向作者复述贡献列表,等确认。
2. **写方法段(Method)**:按边车 §3——先总后分、符号一次定义、每个设计选择给理由、附可复现清单。正确性验证挂 `→ build-oracle` `→ reproduce-result`。
3. **摆实验(Experiments)**:按边车 §4——claim-driven(每个实验对应步骤 1 的一条 claim)、主结果表+消融、每图表配"说明了什么"、公平性交代(挂 `→ contamination-check`)、主动报负面结果(P3)。
4. **写 Related Work**:按边车 §2——主题聚类(非逐篇罗列)、每簇收尾回指本文差异。
5. **回头写 Introduction / Abstract / Conclusion**(此时正文已实):引言按边车 §1 四段式(立地盘→造 gap→问题+具体例子→贡献 bullet);摘要按边车 §5 四句式;结论回答引言提出的问题,不冒新论点(PROSE §2.3 首尾闭合)。
6. **门禁三关**(见下),全过方为完成。

## 门禁

> 三关串行,前关不过不进后关(容忍度档位见 no-fallback-review):
> - **风格关(信号型)**:全文 `→ PROSE_STANDARD.md`。Tier1 词/破折号/三段式/加粗滥用脚本预扫;中庸收尾、超证据结论列信号交作者裁决。
> - **复现关(阻断型)**:方法段过 `→ reproduce-result`(缺数据/超参/种子即拦);实验过 `→ contamination-check`(baseline 不公平即拦);claim 的证据过 `→ build-oracle`(无独立验证即拦)。
> - **审稿关(阻断型,本 SOP 特有 · P2)**:模拟顶会审稿,逐条核对——每条 claim 是否有对应实验证据(claim↔evidence 闭合)?贡献是否被正文兑现(不超证据)?区分"表述问题(可改)vs 方法缺陷(硬伤)"。这一关是 P2 独立 oracle 用在论文上:不信作者自述,拿证据对拍 claim。

[HUMAN] 步骤 1 贡献列表必须作者确认。
[REVIEW] 审稿关必问:"每条 claim 的证据是哪个表/图?找不到的 claim 必须删或补实验。"
[SCAN] PROSE 可机检项(Tier1 词、破折号数、加粗数、"不是X而是Y"正则)。

## 完成判定

- 贡献列表经作者确认,每条可指向正文某节(二值);
- 每条 claim 有对应证据(审稿关 claim↔evidence 映射表无空项);
- 方法段过复现关、实验过污染关(二值);
- 全文过 PROSE 风格关(Tier1 词零命中,其余信号已交作者裁决)。

## 失败处理

遵守 P3:某条 claim 找不到支撑证据 → 删该 claim 或补实验,不得"先写着让它显得贡献多";实验有负面结果 → 如实报告,不得只贴好看的数字;方法段无法复现(缺关键细节)→ 补全或标注"此处不可复现"的诚实声明,不得含糊带过冒充完整;审稿关发现方法硬伤 → 上报作者,不得"用措辞掩盖方法缺陷"。

## 产物

一篇结构合规的论文草稿 + 三项二值确认:贡献↔章节映射表、claim↔evidence 映射表、PROSE 风格关结论(机检输出+待议清单)。
