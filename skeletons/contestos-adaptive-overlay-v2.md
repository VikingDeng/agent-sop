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

对 evidence-bearing research producer/evaluator，`quality-equivalent alternate path` 是 **between-run adaptation**，不是运行时代码分支：失败 run 立即保留并结束，替代实现用显式新配置/代码、新 run ID 和原 acceptance 重新执行。禁止在同一 run 内自动切 method component、model、backend、device、dataset、split、metric、parser 或 analysis 后继续产出证据。synthetic、mock/stub、smoke 与 code-readiness 产物始终 `paper_eligible=false`，不能触发 scientific GO 或进入 authoritative final results。

approved proposal 的原 claim、primary estimand、method 语义、baseline、数据、分析方法、成功标准和正式预算保持独立 verdict。较弱的次级发现可以诚实报告，但不能替换原 contract 的 `SUPPORTED|FALSIFIED|NOT_ESTABLISHED|BLOCKED` 状态；物质改变需要 HUMAN re-contract。

若 fallback 改变 public behavior、research claim、privacy/data boundary、irreversible state 或 material/unbounded cost，停止该越界部分并进入 `MANDATORY_HUMAN_CHECKPOINT` 或 re-contract。只有这些变化需要 HUMAN；工具/模型不可用本身不是项目失败。

## HUMAN 与自适应 checkpoint

当 proposal/spec/claim 已冻结 architecture、strategy 或其他方向时，把 v1 的 architecture/strategy HUMAN checkpoint 记录为 `AUTONOMOUS_CHECKPOINT` 并继续；不得要求 ritual confirmation。只有 genuine unauthorized direction 才暂停，包括 material claim/compatibility change、重大架构或生产依赖、凭据、公开/生产发布、删除/不可逆迁移、法律/隐私选择或显著不可预估成本。

步骤、阶段、工具、模型、review 与中间 checkpoint 可按新证据合并、跳过、重排或替换。硬的是 acceptance criteria、traceability、evidence integrity 与边界，不是 recipe 的形状；reviewer 只能报告具体 failure mode，不能用 taste-only 要求移动冻结 contract。

模型绑定的 package work 不得通过 `resume_agent` 复用已关闭的 role-bound agent；runtime denial 保证该 closed role-bound resume primitive 无法运行。Hook telemetry 不会把 agent ID 绑定到 package/phase、requested role、actual model 或 open state。correction/re-review 应 fresh-spawn 一个显式 typed role；package ID/phase 与 one initial/one correction/one re-review budgets 不变，role/model 改变不会重置 budget。只有在 contract 与 role 均已确认相同的情况下，才可复用仍打开的 agent；实际 model 核验由 supervisor policy 加 PostToolUse/session audit 负责，一旦有 evidence 表明违规就 fail closed。

按不确定性类型路由，而不是只看任务标签。若 Terra 主控及 Luna/Terra 子任务持续在同一核心算法、系统架构或研究执行不变量上枚举近似方案，却没有形成可证伪不变量、判别实验或工件，继续增加同质 token 不算进展。此时优先提出一次紧凑的 `sol_architect` 问题，要求返回具体构造、反例、tradeoff 或 proof obligation；随后主控必须选择可测试路径，或诚实标为 `[UNCERTAIN]` 停止。已有 oracle 或 Terra 正在收敛时不得把 Sol 变成固定阶段，也不得用固定分钟数代替进展判断。

委派必须尊重 critical path。若核心不变量或架构尚未确定并阻断实现，不要提前让 Luna 重新发明架构，也不要让普通 reviewer 在没有工件时做同质搜索；先由主控、判别 oracle 或一次紧凑 architect 关闭该不确定性，再把稳定构造和客观验收交给 Luna。pre-implementation review 只有在问题被写成具体 hypothesis/failure mode 时才有价值。并行的是稳定 sidecar，不是多个 agent 争用同一个未知。

子任务使用能保真的最小自包含上下文：优先 `fork_context=false` 或平台支持的最小 history，并在 compact packet 中给出 objective、scope、当前 artifact/evidence、acceptance 与 stop condition。仓库工件通常比继承多个长 turn 更便宜、更可审计；只有无法压缩的具体依赖才能正当化更多 inherited context。

## Gates 与环境参数

所有 ContestOS 项目的共同 gate 是 claim/contract↔evidence closure 与 no overclaim。reproduction、contamination、statistics、performance、security、human review 等 gate 仅在对应 claim 或风险触发时启用，并记录 `applicable` 或 `not applicable` 的理由。

Review 可使用 `REVIEW_PROFILE=ordinary|api|security|architecture/data` 限定范围。API correctness 需要 Sol risk judgment 时，不自动升级为完整 security workflow；完整 codex-security workflow 只在具体 adversarial security trigger 存在时适用。Skill 是正交 adapter，不能扩大冻结 acceptance、stage 或 artifact；达到 verdict 所需证据即停止，非阻断项进入 backlog 或标为 `[UNCERTAIN]`，尤其是 pre-scale research hardening。

在新 project directory 首次 write、stage 或 commit 前，先用 `git rev-parse --show-toplevel` 确认 root；若目录应独立，使用独立 `git init` 或 worktree。一次只运行一个 full suite；重跑前仅检查/关闭自己此前的 process/session。长任务在每个 decision point 使用一次与 package 复杂度相称的 bounded long wait 与 compact evidence，避免短 polling、重复 raw transcript 读取，并把 monitoring WCU 计入成本记录。wait timeout 只表示“尚未完成”，不是负面 verdict；主控不得在所需子任务仍 open 时直接结束，除非明确取消并记录该 package 未完成。

环境与锁定器由项目生态注入，不得假定 Python 或 uv：使用 `{ENV_CMD}` 准备/验证环境，使用 `{LOCK_CMD}` 生成 `{LOCK_FILE}`，并用项目声明的 verify command 证明可复现。只有 Python/AI 项目选择 uv 时，`uv`/`uv.lock` 才是一个合适的参数实例；它不是 universal default。

## 启用与完成

项目级 `AGENTS.md` 同时引用所选 `contestos-*-v1.md` 和本 overlay。完成时报告：选定的 contract、实际启用的 claim/risk gates、traceability/evidence、fallback 或 HUMAN/re-contract 决策，以及未验证限制。上述优先级与硬锚优先于 v1 中冲突的运行时措辞。
