# 核心纪律(Principles)

> 本仓库全部 skeleton 与 SOP 的共同内核。任何 skeleton / SOP 头部必须声明"落实了下列哪几条"。
> **收纳判据**:一条新 SOP 若无法映射到下列任一纪律,则要么该 SOP 有问题,要么本文件缺一条纪律 —— 必须先在此处补齐纪律,SOP 才能入库。不允许"无纪律归属"的 SOP。

## P1 契约先行(spec-as-contract)

动手前先有可验证的契约:要做什么、**不做什么(non-goals)**、完成判定标准。

- 项目:REQUIREMENTS + NON_GOALS + 验收标准齐全才写实现。
- 运维:变更先写 runbook + 回滚预案。
- 写作:先定读者/目的/非目标/大纲。

## P2 独立 oracle 验证(verify by independent oracle)

正确性用**独立参照**判定,禁止被测对象自证。

- 研究:独立参考实现差分对拍。
- 竞赛:correctness gate 用独立 oracle。
- 开发:验收测试对着 SPEC 写,不对着实现写。
- 运维:健康检查/回滚验证,不靠"我觉得好了"。
- 写作:事实核验,每个论断有据。

## P3 零 fallback / 不造假(fail loud, never fake)

出错/资源不满足/证据不足时**报错或留空,绝不静默降级产出结果**。

- 代码:禁 `except:pass`、禁 `else 降级`、禁 capability-probe fallback;唯一例外是外部 IO 的 bounded retry,耗尽后必须 raise。
- 运维:报警不静默吞,故障不带病降级运行。
- 写作:没依据的数据/引用宁可不写。

## P4 可追溯(traceability)

每个产物能回溯到来源与决策。

- 代码:改动可追溯到需求;关键决策进 ADR。
- 竞赛:每次提交绑 commit + 本地分 + 榜分。
- 写作:每个外部论断绑来源。

## 纪律映射表(维护)

| 纪律 | skeleton 落点 | SOP 落点 |
|---|---|---|
| P1 | 三骨架 spec 层 | 各 SOP 前置条件 |
| P2 | oracle 机制 | build-oracle 等 |
| P3 | §零fallback 章节 | no-fallback-review |
| P4 | manifest/ADR/台账 | commit-and-pr 等 |
