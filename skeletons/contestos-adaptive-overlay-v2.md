# ContestOS legacy compatibility overlay v2.4

> **状态**: legacy, explicit-only compatibility translator。
> **适用条件**: 只有 closest project instructions 明确选择某份 provenance-locked `contestos-*-v1.md` 时才加载。新项目直接使用薄 Domain Profile，不加载 v1 或本文件。
> **来源边界**: v1 原件保持不变；本文件只解释其中与当前 Kernel 冲突的历史措辞，不形成第二套 runtime authority。

## 权威顺序

1. system/developer/user 指令、closest project instructions、冻结的项目 contract；
2. [`PRINCIPLES.md`](../PRINCIPLES.md) 与 [`sop/tier0-core/autonomous-supervisor.md`](../sop/tier0-core/autonomous-supervisor.md)；
3. 与任务匹配的当前 Domain Profile；
4. 本 overlay 对所选 v1 的兼容解释；
5. v1 中未冲突的结构参考与项目 recipe。

固定目录、文件名、步骤数、review 次数、checkpoint、模型、工具、环境管理器或 gate 若与当前 Kernel 冲突，只作为历史建议。硬约束来自结果语义、授权、证据、失败诚实和项目显式选择的 strict profile。

## 共同 canonical mapping

- v1 的 “zero fallback” 表示禁止静默语义降级、伪造成功和改变验收，不表示禁止所有显式 retry 或质量等价替代。
- evidence-bearing research run 例外：失败后不得在同一 run 自动切 method/model/backend/device/data/metric/parser/analysis 后继续产证据；替代路径必须是新配置、新 run ID，并重新接受原验收。
- 已冻结方向可由现有 request/spec/proposal 直接满足 autonomous contract，不要求仪式性 HUMAN checkpoint。只有语义、public/research contract、凭据、隐私、生产/公开、删除/不可逆操作或 material/unbounded cost 越界时等待人。
- 固定 artifact 的存在、Skill、角色、模型或流程状态不能代替结果证据，也不能单独构成 completion gate。
- v1 中的平台、语言、包管理器、目录和服务器值均为参数示例；从 closest project instructions 与实际环境解析，通用 SOP 不猜默认值。

## Development v1 mapping

当前开发语义由 `sop/tier1-skeleton/run-development.md` 提供。v1 的完整目录树、十步 scaffold、`REQUIREMENTS.md`、`NON_GOALS.md`、`ARCHITECTURE.md`、ADR、RUN/PITCH 和固定测试分层只在项目生命周期确实需要时采用。

- spec gate 要求 outcome、non-goals、范围和验收在语义上足够明确，不要求指定文件物理存在；
- 0→1 产品从用户能力、domain/state model、关键 journeys 和适用 lifecycle 推导完整性，不把某个 CRUD/页面清单推广为所有项目门禁；
- comparison、持久化、身份、错误状态和真实 UI 渲染只在产品 claim 触发时验收，具体实现与 viewport/tool 由项目和 Oracle 决定；
- dependency、security、performance、release 与 independent review 按实际风险触发，不因 v1 表格无条件执行。

## Research v1 mapping

当前 approved AI proposal 实现由 `sop/tier1-skeleton/research-execution-grill.md` 与 `run-experiment.md` 提供。原 claim、primary estimand、method 语义、baseline、数据/split、analysis、成功标准和正式预算各自保留；smoke、synthetic、mock/stub 与 code-readiness 始终 `paper_eligible=false`。

v1 的固定远程路径、uv、目录、签名和 gate 链不是默认要求。远程资源从项目/local adapter 发现；统计、contamination、scale、profiling 和独立 review 只在 claim 或失败风险触发。signed v3 仅在项目明确选择高保证协议时完整启用。

## Competition v1 mapping

当前通用竞赛语义由 `sop/tier1-skeleton/run-competition.md` 提供。v1 的性能赛主轴、四类互斥标签、完整 `contests/` 树和 local-proxy-first 是历史 recipe。

- 按判定、反馈、工件、环境、事件和外部动作包络组合真实赛制；
- 产品黑客松组合 Development Profile，研究工件按 claim 组合 Research Profile；
- 官方 checker/evaluator 优先，proxy、profiler、patch series、holdout、ledger 与多轮 review 仅在对应未知量触发；
- package 只生成 submission-ready 工件，不等于注册、上传、部署、公开或消耗提交预算；
- deadline、final reserve、last-known-good 和平台 receipt 属于竞赛结果边界，不能被一般开发完成状态替代。

## 启用与迁移

legacy 项目在项目级指令中同时引用：选中的 v1、本 overlay、当前 Kernel 和相应 Domain Profile。新项目只引用 Kernel 与 Domain Profile。迁移完成后删除项目对 v1/overlay 的运行时引用，但保留本仓 provenance 文件，不回写历史来源。
