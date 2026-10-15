# 宏观结构：读者在每个节点获得什么

分析 A2、B1、B3 三篇的章节推进。三篇文种不同（中文期刊综述、工程设计提案、设计提案），共同点是每个宏观节点都让读者拿到一个明确收获，并引出下一节要回答的问题。**这不是目录抄写**：重点是前一节为后一节提供了什么。条目只覆盖已核对过的片段与做法。

---

## A2 移动应用GUI测试自动生成技术综述

**来源**：王博等，《软件学报》2025, 36(6): 2713-2746 — https://www.jos.org.cn/html/2025/6/7313.htm ｜ **访问**：2026-09-21 ｜ **复核**：confirmed

**实际阅读范围**：§1 引言全文，§3 章首与 §3.1 / §3.2.1 / §3.2.2 / §3.3 章首 / §3.4 小结，§4–§6 全文；§2、§3.1.2、§3.3.1 只读到部分；§3.3.2–§3.3.5 正文、图 1–图 3 的图像内容、145 条参考文献未读，未逐页核对 PDF 排版。**分类正文没有逐字读完**，本条不声称全文对应。

**短摘录**：

> 而与文献[ 3 , 5 ]等针对一般GUI测试生成的文献不同, 本文聚焦于分析移动平台应用交互特点, 并不涉及传统桌面应用的GUI测试.

**章节顺序，以及它为什么成立**：

```text
§1 引言：问题 → 背景 → 移动端与桌面端的机制性差异 → 写作目的 → 检索口径
     → 统计证据（表1、图1）→ 与已有综述逐条比较 → 贡献(1)–(5) → 全文导航
§2 研究框架与形式化定义
§3 分类：先承认已有的四维度 → 给出本文三维度 → 声明主线是「测试动作序列生成策略」
→ §4 数据集与工具：纳入规则 → 清单（表7/8/9）→ 截止时点
→ §5 挑战（§5.1）与未来方向（§5.2）→ §6 总结（只回收）
```

同一主题在 2019—2022 年已有多篇综述，§1 因此要回答「凭什么还要再写一篇」：先写缺口，再给可核对的增量（新增已有综述未覆盖的参考文献 83 篇）。读者接受了增量与检索口径，§3 的分类才有必要读；§3 先承认既有维度再声明主线，三个维度才不会被当成等价并列；§5.2 的每条方向才能对上 §5.1 的一条挑战。

**读后收获**：范围与非目标写成「与〈可指名的文献〉不同，本文聚焦于…，并不涉及…」，对照对象能被读者打开；收录口径 = 检索式 + 来源库 + 时间窗 + 条数 + 取舍规则；清单先规则后时点；挑战与展望一一对应。

**不能照搬**：该文依赖同行评议文献总体与 CCF 评级，内部报告照搬「表 1 发表源统计」会造出无依据的统计；「贡献(1)–(5) + 全文导航」是期刊综述的体例件；文中对领域演化的叙述依据发表时间序列，不是因果实验。

---

## B1 KEP-1287: In-place Update of Pod Resources

**来源**：Kubernetes SIG Node — https://www.kubernetes.dev/resources/keps/1287/ ｜ **访问**：2026-09-21 ｜ **复核**：confirmed

**实际阅读范围**：首选页在 Design Details → Future Enhancements 处被抓取工具截断；同一文档的 README 源补读到 Test Plan 至 Alternatives 全文（两个来源文字一致，只有列表序号渲染不同）。逐字核对的是 Non-Goals 与 Risks and Mitigations 两节；Instrumentation 六个指标的逐行表述、Test Plan 全部 e2e 用例、PRR 问卷每处问答未逐行核对。

**短摘录**：

> This should be handled by actors which initiated the resizing.

**章节顺序，以及它为什么成立**：

```text
Release Signoff Checklist（哪些还没勾）→ Summary → Motivation（Goals / Non-Goals）
→ Proposal（API Changes → Risks and Mitigations）→ Design Details → Test Plan
→ Graduation Criteria → Upgrade / Downgrade → Version Skew → PRR Questionnaire
→ Implementation History → Drawbacks → Alternatives（Option 1/2/3 的 Pros/Cons）
```

Summary 先给做什么与当前状态，读者才带着「这次做到哪一步」读 Goals / Non-Goals；Non-Goals 首句给出显式非目标后紧跟一句责任移交，读者当场知道边界归谁。Design Details 给出机制与状态之后，Test Plan 与 Graduation Criteria 才有验收对象。Alternatives 放在最后：读者此时已掌握判据，可以直接比较 Option 1/2/3，而不是先读被否方案。

**读后收获**：风险条目写成「触发条件 → 可观测后果（状态字段、错误名、指标）→ 处置或范围声明」；不处置的风险单独成条，用 `but` 把「将来可能考虑」限定为不承诺；`Currently (v1.35)`、`out-of-scope for this KEP` 这类限定词把当前实现与长期承诺分开；Release Signoff Checklist 里两项 PRR 未勾选，交付状态没有被正文粉饰。

**不能照搬**：KEP 有强制模板、Release Signoff Checklist 与 SIG 审批链，内部文档没有对应验收机制；`OutOfCPU` / `InPlacePodVerticalScaling` 等名称依赖 Kubernetes API 语境；英文条目「名词短语开头 + 条件从句」直译成中文会变成无主语长句。

---

## B3 RFC 2094: Non-lexical lifetimes

**来源**：The Rust RFC Book — https://rust-lang.github.io/rfcs/2094-nll.html ｜ **访问**：2026-09-21 ｜ **复核**：partly_confirmed

标题统一取 **RFC 2094: Non-lexical lifetimes (2017-08-02)**：日期来自页面 `Start Date`，页面书名 `2094-nll - The Rust RFC Book` 只在这里附注；页面无作者署名与年份。

**实际阅读范围**：首选 HTML 页在 §How We Teach This 处被渲染截断（页面自注 “Omitted 24509 bytes”），尾部小节经 raw markdown 全文读到。§Drawbacks、§Alternatives（含两个子节）、§Unresolved questions、§Appendix 开头逐字读；Detailed design 的 Layer 1–5 推导正文与 Appendix 后两段未逐字通读。

**短摘录**：

> There are very few drawbacks to this proposal. The primary one is that the rules for the system become more complex. However, this permits us to accept a larger number of programs, and so we expect that using Rust will feel simpler.

**章节顺序，以及它为什么成立**：

```text
Summary（做什么 + 剩余限制在哪节）
→ Motivation（What is a lifetime? / Problem case #1–#4 / 方案轮廓）
→ Detailed design（Layer 0–5）→ How We Teach This → Drawbacks
→ Alternatives（含两个子节）→ Unresolved questions
→ Appendix: What this proposal will not fix
```

Motivation 用带代码的失败案例先让读者接受「需要改」，Detailed design 才展开机制。Drawbacks 先给代价与对价，Alternatives 的比较才有判据，且所有被否方案复用同一检验例。Unresolved questions 全节只有 `None at present.`，不为凑条目编未决项；明确不做的另立 Appendix，并由 Summary 末句指路，读者在第一节就能判断范围。

**读后收获**：代价写清落在系统的哪一部分、给出对价，并把「预期」与「已发生」分开措辞——该节说的是**主要的一项代价**（rules 变复杂），开头的 `very few drawbacks` 说明并不止这一项；换来的对价是能**接受更多程序**，用 `we expect` 标明是预期。被否方案写「机制 → 弃用或保留理由」，对失败方案也写它能解决什么；未决项如实写「目前没有」。

**不能照搬**：RFC 的固定小节来自提案模板与公开评审流程；§Drawbacks 四句能成立，依赖原型仓库、tracking issue 与公开讨论作外部证据链，内部文档没有这层背书就要自己给数据；Alternatives 用 RFC 编号与 PR 链接引用前作，中文交付一般走 `references.bib`；文中第一人称判断在需要机构署名的文档里要另行决定。

---

宏观上的检查动作见 [principles.md](principles.md) 第 4–6 条；边界例（A1、A3、B2、D2）见 [boundary-cases.md](boundary-cases.md)。
