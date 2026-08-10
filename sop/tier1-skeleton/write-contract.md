# SOP-write-contract: 写契约(spec 先行)

- **层级**: tier1-skeleton
- **落实纪律**: P1(契约先行,含 non-goals)
- **绑定骨架**: development
- **通用性档位**: U1(spec 结构通用,验收标准内容项目相关)
- **版本**: v2

## 触发条件

development 骨架项目开工前,或新增一块功能前——**没有契约不许写实现代码**(spec gate)。

## 前置条件

有一个待交付的目标(项目或功能),且验收标准可从 stakeholder 的明确描述、现有 spec、测试或行为契约中推出。

## 依赖 SOP

→ tier0-core/autonomous-supervisor.md(判定 autonomous / interactive / mandatory human checkpoint)。

## 步骤

1. 写 `spec/REQUIREMENTS.md`:每条需求**可测**——给出"怎样算满足"的可观测判据。
2. 写 `spec/NON_GOALS.md`:明确**不做什么**(压 scope creep),把反需求提到与需求同等地位。
3. integrated 项目:写 `contracts/CONTRACT.md`——public API 表面冻结、SemVer 策略、废弃策略、行为契约(语义/错误码/幂等)。
4. 关键设计决策记 `spec/DECISIONS.md`(ADR):记 why,防跨 session 上下文断裂。
5. 对照 `→ tier0-core/autonomous-supervisor.md` 判定 checkpoint:
   - 目标明确、判据可测、修改在授权 workspace 内且不涉及 public API/兼容承诺、产品语义、重大生产依赖、凭据、发布、数据删除或不可逆迁移时,Supervisor 可用 `AUTONOMOUS_CHECKPOINT` 冻结契约并继续;记录契约来源、假设、授权范围和验收判据。
   - 用户要求阶段同步但方向无分叉时可用 `INTERACTIVE_CHECKPOINT`;同步不把日常执行交还用户。
   - 产品语义、public API/兼容承诺、重大架构方向、重大生产依赖、凭据、发布、删除或不可逆决策,以及缺少关键需求只能靠猜时,必须 `MANDATORY_HUMAN_CHECKPOINT`。
6. 自动冻结后仍按契约施工;出现新方向分叉或验收标准变化时重新进入步骤 5,不得边做边猜。PR 可承担异步人类终审,不替代命中 mandatory 条件时的方向决策。

## 门禁

[AUTO] REQUIREMENTS + NON_GOALS + 每条可测验收标准存在,才解锁写实现。
[AUTO] 授权包络内存在 `AUTONOMOUS_CHECKPOINT` 留痕(目标/来源/假设/范围/验收标准),才可自动解锁。
[HUMAN] 产品语义、public API/兼容承诺、重大架构或不可逆决策,以及只能靠猜的关键需求,必须人工确认。

## 完成判定

- REQUIREMENTS(每条可测)+ NON_GOALS 存在并定稿;
- integrated 项目 CONTRACT.md 存在;
- checkpoint 记录为已完成的 autonomous/interactive checkpoint,或已获得 mandatory human checkpoint 的方向确认(二值可查)。

## 失败处理

遵守 P3:验收标准写不出"可测判据"→ 该需求视为未定义,不得"边做边明确"就开写(那是 scope creep 温床);无法从明确任务、spec、测试或行为契约得到关键方向 → 停在 mandatory human spec gate 报告阻塞,不得借自主模式猜测;禁止先写实现再补 spec(spec 追着实现写=自证);自动冻结不等于降低契约强度,缺少 checkpoint 留痕不得放行。

## 产物

`spec/REQUIREMENTS.md` + `spec/NON_GOALS.md` +(integrated)`contracts/CONTRACT.md` + `spec/DECISIONS.md` + checkpoint 类型/来源/假设/授权范围/验收标准记录。
