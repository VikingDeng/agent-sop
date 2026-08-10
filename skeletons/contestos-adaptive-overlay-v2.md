# ContestOS 自适应运行时 overlay v2

> **状态**: active operational overlay。适用于选中的任一 `contestos-*-v1.md`。
> **来源边界**: v1 原件 provenance-locked；本文件只提供运行时解释与参数化，不回写、不伪装成 v1 原文。

## 权威与优先级

1. 用户任务、项目 spec/claim 与明确授权冻结的产品/研究方向。
2. 本 v2 overlay：对 v1 runtime wording 的冲突解释具有 active authority。
3. 所选 ContestOS v1 原件：目录结构、来源声明与本文件未覆盖的硬锚继续有效。
4. 通用 SOP 与项目 recipe：提供可替换的执行路径，但不得降低前述验收与边界。

如果 v1 的“零 fallback”、固定 HUMAN checkpoint、uv 锁定或无条件 gate 与本文件冲突，按 v2 执行；v1 文件内容仍保持不变。

## 不可移动的硬锚

- 关键输入、决策、commit/manifest、提交产物与证据保持可追溯。
- correctness/claim 的关键判断使用独立或足够独立的 evidence；不得用被测对象自证关键结果。
- 不得伪造成功、隐藏失败、冒充旧结果或改变 acceptance 以通过门禁。
- 隐私/数据边界、不可逆状态、公开兼容与未授权的 material/unbounded cost 仍是硬边界。

## Fallback 的 canonical semantics

v1 的“zero fallback”只表示：禁止**静默语义降级、fabricated success 与 altered acceptance**。允许显式、quality-equivalent 的 alternate tool/model/implementation path；替代路径必须披露触发原因，并以未改变的 acceptance 和匹配的 oracle 重新验证。

若 fallback 改变 public behavior、research claim、privacy/data boundary、irreversible state 或 material/unbounded cost，停止该越界部分并进入 `MANDATORY_HUMAN_CHECKPOINT` 或 re-contract。只有这些变化需要 HUMAN；工具/模型不可用本身不是项目失败。

## HUMAN 与自适应 checkpoint

当 proposal/spec/claim 已冻结 architecture、strategy 或其他方向时，把 v1 的 architecture/strategy HUMAN checkpoint 记录为 `AUTONOMOUS_CHECKPOINT` 并继续；不得要求 ritual confirmation。只有 genuine unauthorized direction 才暂停，包括 material claim/compatibility change、重大架构或生产依赖、凭据、公开/生产发布、删除/不可逆迁移、法律/隐私选择或显著不可预估成本。

步骤、阶段、工具、模型、review 与中间 checkpoint 可按新证据合并、跳过、重排或替换。硬的是 acceptance criteria、traceability、evidence integrity 与边界，不是 recipe 的形状；reviewer 只能报告具体 failure mode，不能用 taste-only 要求移动冻结 contract。

## Gates 与环境参数

所有 ContestOS 项目的共同 gate 是 claim/contract↔evidence closure 与 no overclaim。reproduction、contamination、statistics、performance、security、human review 等 gate 仅在对应 claim 或风险触发时启用，并记录 `applicable` 或 `not applicable` 的理由。

环境与锁定器由项目生态注入，不得假定 Python 或 uv：使用 `{ENV_CMD}` 准备/验证环境，使用 `{LOCK_CMD}` 生成 `{LOCK_FILE}`，并用项目声明的 verify command 证明可复现。只有 Python/AI 项目选择 uv 时，`uv`/`uv.lock` 才是一个合适的参数实例；它不是 universal default。

## 启用与完成

项目级 `AGENTS.md` 同时引用所选 `contestos-*-v1.md` 和本 overlay。完成时报告：选定的 contract、实际启用的 claim/risk gates、traceability/evidence、fallback 或 HUMAN/re-contract 决策，以及未验证限制。上述优先级与硬锚优先于 v1 中冲突的运行时措辞。
