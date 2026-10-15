# 微观结构：句子与段落之间

分析 C1、C2、D1、D3 四条的段落推进。四篇文种不同（语言教程章节、产品参考手册、官方故障复盘、IETF 规范），共同点是把「段落里为什么这么排」写实：读者在每段的疑问能指认，句子的功能与依赖能拆出来。条目只覆盖已核对过的片段与做法。

---

## C1 Python 浮点章节 §15.1 Representation Error

**来源**：Python 3.14.7 文档《15. Floating-Point Arithmetic: Issues and Limitations》§15.1 — https://docs.python.org/3/tutorial/floatingpoint.html ｜ **访问**：2026-09-21 ｜ **复核**：confirmed

无具名作者；页脚 © 2001 Python Software Foundation，PSF License v2。页面没有发布年份，可见的时间标记只有版本号与页脚 “Last updated on Sep 21, 2026”。

**实际阅读范围**：该单页全文，含第 15 章导言、§15.1 正文、全部 `>>>` 代码块与结尾的 `fractions` / `decimal` 示例。未打开页内任何链接，包括外部延伸阅读与 GitHub 上的 `.rst` 源文件。

**短原文**：

> Why is that? 1/10 is not exactly representable as a binary fraction. Since at least 2000, almost all machines use IEEE 754 binary floating-point arithmetic, and almost all platforms map Python floats to IEEE 754 binary64 “double precision” values.

**每句的贡献与依赖**：

- 导言：机制总述 → 现象（`0.1 + 0.1 + 0.1 == 0.3` 返回 `False`）→ 十进制类比（1/3 写成 0.3、0.33、0.333）→ 二进制类比（0.1 是无限循环）→ 显示层掩盖差值 → 可复现反例 → 可行的比较方式（`math.isclose`、`round`）→ 归因（不是 Python 的 bug，也不是你的代码的 bug）→ 处置清单。类比先给直觉，读者才接受「1/10 不能精确表示」；归因句排在现象句之后。
- §15.1：目标句 → 前置限定 `Basic familiarity with binary floating-point representation is assumed.` → 定义 representation error → 把对象扩到 Python/Perl/C/C++/Java/Fortran，阻断「这是某个语言的缺陷」的读法 → 自问自答 `Why is that?` 给机制（IEEE 754 binary64、53 位）→ 四段整数演算把「N 的最佳值是 56」变成能返回 `True` 的判据 → 两个方向的偏差收成排他结论 → 末尾模块调用的输出与正文推导出同一个数。

**读者可用于什么判断**：知道「显示短」不等于「值相同」，也知道该用哪种方式比较浮点；这类结论的确定性来自 IEEE 754 下可判定的恒等，同样的语气不能挪到性能、数据质量、模型行为这类经验性结论上。

**边界**：该节用 `>>>` 会话充当证据，因为教程读者会照着敲；换到报告或规范里，证据形式要按读者任务换成可复现脚本加输出、表格或编号代码块——不是「正式文档禁止 REPL」。

---

## C2 TiDB 事务隔离级别：「与 ANSI 可重复读隔离级别的区别」

**来源**：PingCAP TiDB 文档中心 — https://docs.pingcap.com/zh/tidb/stable/transaction-isolation-levels/ ｜ **访问**：2026-09-21 ｜ **复核**：confirmed

无具名作者、无发布日期；版本选择器显示的 v8.5 是文档集版本，不是文档年份。

**实际阅读范围**：该页正文全文。取全文经同域 `.md` 路由，另用 stable HTML 页与 `pingcap/docs-cn` 仓库同名文件交叉比对，正文逐段一致。页内所有外链目标页均未打开。

**短原文**：

> 该隔离级别不会出现狭义上的幻读 (A3)，但不会阻止广义上的幻读 (P3)，同时，SI 还会出现写偏斜，而 ANSI 可重复读隔离级别不会出现写偏斜，会出现幻读。

**每句的贡献与依赖**：该小节四步——让步（名称虽然也是可重复读）→ 判据来源（指名 *A Critique of ANSI SQL Isolation Levels*）→ 归类结论（TiDB 实现的是论文中的快照隔离 SI）→ 具名行为对照（A3 / P3 / 写偏斜）。让步句先消掉「名字相同即语义相同」的默认假设，判据句才有位置；归类结论是行为条目的依据，而行为条目全部落在具体异常名上，读者不必自己把「有差异」翻译成能改的测试。整页顺序同样是先给背景与 SQL-92 对照表、再给页面级结论与注意块，最容易被误用的例外排在读者据此选型之前。

**读者可用于什么判断**：能区分「沿用名称」与「具体行为」，知道按 ANSI 或 MySQL 可重复读的预期写业务代码时哪些异常挡不住，也知道限制在哪种事务模式下生效。

**边界**：产品参考手册允许并依赖「本产品 vs MySQL vs ANSI 标准」的立场化对照；换成没有单一实现对象的原理性文档或跨实现调研，这种写法会退化成产品宣传口径。该页的差异结论靠一篇外部论文与实现声明支撑，页内没有实测数据；「不建议开启自动重试」只给后果加外链，机制不在本页。本条不承担全面数据库事实核验。

---

## D1 Cloudflare 2019-07-02 复盘：「What happened」

**来源**：Cloudflare Blog — https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/ ｜ **访问**：2026-09-21 ｜ **复核**：partly_confirmed

署名 John Graham-Cumming。**2019-07-12 是发布时间**，2026-09-21 是本次访问日期。页面另标 `dateModified` 为 2026-07-15，本条目如实保留这个观察，但不据此推断正文一定变化。

**实际阅读范围**：正文 9 个小节全文，含 WAF 正则的逐字文本；图像与视频只见图注或替代文字，页面底部导航与订阅表单未读。取全文用 `curl`，`web_fetch` 只返回导航。

**短原文**：

> At 14:00 the WAF was identified as the component causing the problem and an attack dismissed as a possibility. The Performance Team pulled live CPU data from a machine that clearly showed the WAF was responsible. Another team member used strace to confirm. […] Eventually, a team member executed the global WAF termination at 14:07 and by 14:09 traffic levels and CPU were back to expected levels worldwide.

**每句的贡献与依赖**：首句 `All times in this blog are UTC.` 先定时间基准，紧接着 13:42 部署；`Three minutes later` 推进到首次告警——13:45 由它推算得出，与字面时刻分开记。现象扩散段把单点合成测试告警升级为全网现象，`rapidly followed by` … `and then` 承担范围扩张而非并列；假设（`speculation`）与后面的 `dismissed as a possibility` 构成先立后破。根因定位写成三条并列的证据动作，每条带对象与工具；处置受阻单独成段、列出三项阻碍，「提出方案 → 执行」之间的 5 分钟因此有归属。验证段写清做法与范围：负向测试验证「是否真是该变更导致」，正向测试验证回滚是否生效，范围限定为一个城市、部分流量、且剔除付费客户流量。

**状态与读者判断**：「What's happened since last Tuesday」用 `(Done)` / `(Inspection complete)` / `(ETA: July 19)` / `(ETA: July 31)` 标出一部分条目——`Inspection complete` 是**检查已完成**；同一清单里其余条目与紧随其后的一段长期计划没有状态标签，那只是页面上没标，不等于未完成。读者据此能自己算出间隔（部署→首次告警 3 分钟、提出方案→执行 5 分钟、执行→恢复 2 分钟），也能分清已处置、已检查、计划中与未标状态。

**边界**：这是企业对自身事故的公开 post-mortem，带对外致歉与品牌修复功能；作者能拿到活体 CPU 曲线、`strace` 输出与内部截图，多数文档作者没有这种一方数据，缺证据就标「未决」，不模仿其确定性语气，也不虚构同等精度的时刻。机制解释整体推到文末 Appendix，面向要立刻改配置的运维读者，这种推迟不够用。

---

## D3 RFC 2119 §3 SHOULD

**来源**：RFC 2119 / BCP 14，S. Bradner（Harvard University），1997 年 3 月 — https://www.rfc-editor.org/rfc/rfc2119.html ｜ **访问**：2026-09-21 ｜ **复核**：partly_confirmed

另用 RFC 8174 核对它对 RFC 2119 的更新点；本条记录的字段都取自 rfc2119.html 这一页。

**实际阅读范围**：整页解码文本，Status of this Memo、Abstract、§1–§9 逐节读完；未查看 HTML 源码与页面导航。

**短原文**：

> This word, or the adjective "RECOMMENDED", mean that there may exist valid reasons in particular circumstances to ignore a particular item, but the full implications must be understood and carefully weighed before choosing a different course.

**每句的贡献与依赖**：§3 只有一句，内部四步——词义映射 → 允许偏离的条件 → 偏离方必须完成的判断义务 → 时序（`before choosing a different course`）。§4 在相同位置换成弱情态词，强度差是句法可见的。§5 把 MAY 的自由度翻成相邻方两条对称的 `MUST be prepared to interoperate`，「可选」因此变成两侧的确定义务；§6 给最高强度词加上使用门槛：互操作，或可能造成危害。§1 与 §2 对称并列，谓语只差 requirement / prohibition 一个词，且都不带例外从句。

**读者可用于什么判断**：能判断一条 SHOULD 是否真的可偏离——有没有写出允许偏离的条件和偏离前必须完成的动作；也能区分「文档没写后果」与「这件事没有后果」，RFC 2119 把不遵守的后果交给具体文档，§7 只提醒安全影响可能很 subtle。

**边界**：这是给规范作者看的元文档，定义的是词而不是系统行为，词表本身不产生验收标准；它背后有 IETF 的互操作审查制度承担「谁判定不合规、判定后怎么处理」，内部文档没有这一层，必须自己写清。RFC 8174 把特殊含义限定为「仅全大写时」，中文没有大小写手段，只能靠显式词表加格式约定。

---

微观上的检查动作见 [principles.md](principles.md) 第 1–3、7 条；边界例见 [boundary-cases.md](boundary-cases.md)。
