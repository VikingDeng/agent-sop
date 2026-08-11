# SOP-package-submission: 核验并冻结提交工件

- **层级**: tier1-skeleton
- **落实纪律**: P2(提交候选与验收证据同源) P3(禁止隐藏失败/改口径) P4(工件可识别与可追溯)
- **绑定骨架**: competition；development(产品型黑客松组合材料)
- **通用性档位**: U1(提交形态通用；平台格式、重建方式与证据由项目注入)
- **版本**: v3

## 触发条件

需要把一个候选冻结成可上传/交付给评测机、评委、代码 review 或现场 demo 的准确 bundle 时。它覆盖源码/patch/二进制、notebook、CSV/模型/output、agent/API、仓库/PR、运行应用及 repo+URL+video+deck+form 等组合工件。

本 SOP **只完成本地打包与核验，不执行注册、上传、部署、公开、final selection 或其他外部提交**；这些动作由 `run-competition` 的授权包络控制。

## 前置条件

- contest contract 已给出 `{SUBMIT_FORMAT}`、必需文件/链接/字段、大小/运行/资源/许可规则与当前候选；
- 对当前候选适用的 correctness、格式、运行、rubric 或 score evidence 已达到提交阈值；并非所有赛制都有二值 correctness gate；
- 候选有足够的 source identity：可为 Git commit、平台 version、不可变 snapshot、archive 或现有工件 ID。Git 项目只有在 dirty state 会导致候选不清或无法恢复时才要求 clean commit。

## 依赖 SOP

→ tier0-core/build-oracle.md(按工件 claim 选择 checker/evaluator/rubric evidence)

→ tier0-core/commit-and-pr.md(Git 是实际 source-of-truth 且需要持久交付时使用)

→ tier1-skeleton/maintain-patch-series.md(官方要求 patch 或已明确选择 upstream isolation 时使用)

## 步骤

1. 从权威规则列出这次 bundle 的**实际**组成和校验方式。单文件算法题只核验源文件/语言；Kaggle 类核验列名、行数与运行限制；agent/runtime 核验 interface、依赖、timeout/checkpoint；黑客松核验 repo、可用部署、必用 partner tech、demo/video/deck、说明和表单字段。未要求的材料不顺手加入。
2. 冻结一个候选身份，并从该候选生成 bundle。运行 checker/benchmark/demo 的必须是将要提交或平台将从其构建的同一版本；若平台接受 URL/部署，记录实际可访问版本而不是仅记录本地源码。
3. 用平台原生 validator/checker 或最接近官方的本地验证检查格式、入口、依赖、资源、许可/披露与关键行为。需要重建时按平台真实流程 smoke；只有规则比较字节、要求 exact patch/archive，或字节差异本身影响 verdict 时才要求 byte-identical rebuild。
4. 保存或指向这份准确 bundle，附足以回答“交了什么、从哪里来、通过什么验证”的最小 provenance。单次、单文件、当前 session 内可恢复的提交不强制 `manifest.json`、`IDEA.md`、SHA256 或 `submissions/{sub_id}/` 目录。
5. 只有多次候选、稀缺提交、跨 session、组合材料或本地/线上错配风险存在时，追加轻量 manifest/ledger：candidate ID、source identity、时间、关键 evidence、提交理由、预算状态与待回填 receipt。profile/patch/local score 字段只在实际存在时记录。
6. 输出 submission-ready 状态与 remaining blockers；外部动作尚未授权时停在这里。已授权时，把同一 bundle 交还 `run-competition` 执行平台动作，打包阶段不自行消耗提交次数。

## 门禁

- `[BLOCK]` bundle 缺官方必需项、格式/入口/资源/许可不合规，或当前候选的关键 verdict 已失败；
- `[BLOCK]` 本地验证对象与将提交/部署对象不同源，或组合材料中的 URL、视频、仓库与声称功能不一致；
- `[BLOCK]` 通过关闭正确性、隐藏 unsupported case、切换未披露数据/模型/精度或只测不会进入提交路径的代码来制造分数；
- `[SIGNAL]` 规则允许且官方 evaluator 会真实测量的慢路径/兼容路径不是自动作弊；只有它绕过目标路径、改变 claim 或令本地 evidence 与提交路径不一致时才阻断；
- `[HUMAN]` 本 SOP 不把“bundle ready”解释为外部动作授权。

## 完成判定

- 有一份满足 `{SUBMIT_FORMAT}` 与所有适用规则的准确 bundle/版本引用；
- 它与关键验证证据同源，并通过平台原生或最接近官方的可行核验；
- provenance 强度足以在当前生命周期识别/恢复候选；exact rebuild、clean tree、manifest 与 ledger 仅在规则/风险触发时成立；
- 状态明确为 `submission-ready`，没有冒充已上传、已部署或已获官方 verdict。

## 失败处理

格式或 validator 失败时保留原错误并修复同一候选；修复改变行为时重跑受影响证据。无法复刻平台构建时报告 packaging uncertainty，可在已有授权包络内用廉价 smoke 校准，但不能把本地成功写成线上通过。dirty tree 只有在无法准确冻结/恢复候选时才阻断；否则保存准确 snapshot 或 commit 后继续。慢/兼容路径按官方规则和实际评分路径判断，不按 `fallback` 关键字零容忍。

## 产物

一份 submission-ready bundle 或不可变版本引用、适用验证结果和最小 provenance。manifest、ledger、submitted-files 快照、local score、profile、patch、idea、demo/video/deck 与规则披露均按赛制和生命周期条件产生，不创建固定空目录树。
