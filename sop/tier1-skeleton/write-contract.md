# SOP-write-contract: 写契约(spec 先行)

- **层级**: tier1-skeleton
- **落实纪律**: P1(契约先行,含 non-goals)
- **绑定骨架**: development
- **通用性档位**: U1(spec 结构通用,验收标准内容项目相关)
- **版本**: v1

## 触发条件

development 骨架项目开工前,或新增一块功能前——**没有契约不许写实现代码**(spec gate)。

## 前置条件

有一个待交付的目标(项目或功能),且 stakeholder 可确认验收标准。

## 依赖 SOP

无(是开发链路的起点)。

## 步骤

1. 写 `spec/REQUIREMENTS.md`:每条需求**可测**——给出"怎样算满足"的可观测判据。
2. 写 `spec/NON_GOALS.md`:明确**不做什么**(压 scope creep),把反需求提到与需求同等地位。
3. integrated 项目:写 `contracts/CONTRACT.md`——public API 表面冻结、SemVer 策略、废弃策略、行为契约(语义/错误码/幂等)。
4. 关键设计决策记 `spec/DECISIONS.md`(ADR):记 why,防跨 session 上下文断裂。
5. 契约定稿需 [HUMAN] 介入确认(spec 与架构是人工把关点)。

## 门禁

[AUTO] REQUIREMENTS + NON_GOALS + 每条可测验收标准存在,才解锁写实现。
[HUMAN] spec / CONTRACT / ARCHITECTURE 定稿处人工确认。

## 完成判定

- REQUIREMENTS(每条可测)+ NON_GOALS 存在并定稿;
- integrated 项目 CONTRACT.md 存在(二值:文件+人工确认)。

## 失败处理

遵守 P3:验收标准写不出"可测判据"→ 该需求视为未定义,不得"边做边明确"就开写(那是 scope creep 温床);stakeholder 无法确认验收标准 → 停在 spec gate 报告阻塞,不得跳过契约直接实现;禁止先写实现再补 spec(spec 追着实现写=自证)。

## 产物

`spec/REQUIREMENTS.md` + `spec/NON_GOALS.md` +(integrated)`contracts/CONTRACT.md` + `spec/DECISIONS.md`。
