# ContestOS 自适应兼容 overlay v2.1

> **状态**: active compatibility overlay。适用于选中的任一 `contestos-*-v1.md`。
> **来源边界**: v1 原件 provenance-locked；本文件只把其历史运行时措辞翻译到 `autonomous-supervisor` 的当前语义，不回写、不伪装成 v1 原文，也不形成第二套 runtime authority。

## 权威与优先级

1. 用户任务、closest project instructions、项目 spec/claim 与明确授权冻结的产品/研究方向。
2. `PRINCIPLES.md` 的不变量与 `sop/tier0-core/autonomous-supervisor.md` 的通用运行时决策；Supervisor 是唯一通用 runtime source。
3. 本 overlay：只解释所选 v1 中与当前运行时冲突的措辞。
4. Tier-1 SOP、所选 ContestOS v1 原件与项目 recipe：提供领域约束、结构参考和可替换路径；固定 artifact/step/gate 只有在 claim、风险、生命周期或显式 strict profile 触发时适用。

如果 v1 的“零 fallback”、固定 HUMAN checkpoint、uv 锁定、固定目录/文档或无条件 gate 与 Supervisor 及本 overlay 冲突，按当前自适应语义执行；v1 文件内容与来源声明仍保持不变。

## 不可移动的硬锚

- 关键输入、决策、commit/manifest、提交产物与证据保持可追溯。
- correctness/claim 的关键判断使用独立或足够独立的 evidence；不得用被测对象自证关键结果。
- 不得伪造成功、隐藏失败、冒充旧结果或改变 acceptance 以通过门禁。
- 隐私/数据边界、不可逆状态、公开兼容与未授权的 material/unbounded cost 仍是硬边界。

## Fallback 的 canonical semantics

v1 的“zero fallback”只表示：禁止**静默语义降级、fabricated success 与 altered acceptance**。允许显式、quality-equivalent 的 alternate tool/model/implementation path；替代路径必须披露触发原因，并以未改变的 acceptance 和匹配的 oracle 重新验证。

若 fallback 改变 public behavior、research claim、privacy/data boundary、irreversible state 或 material/unbounded cost，停止该越界部分并进入 `MANDATORY_HUMAN_CHECKPOINT` 或 re-contract。只有这些变化需要 HUMAN；工具/模型不可用本身不是项目失败。

## HUMAN 与自适应 checkpoint

当 proposal/spec/claim 已冻结 architecture、strategy 或其他方向时，现有 compact contract 即可作为 autonomous freeze 并继续；不得额外要求 checkpoint 文件或 ritual confirmation。只有 genuine unauthorized direction 才暂停，包括 material claim/compatibility change、重大架构或生产依赖、凭据、公开/生产发布、删除/不可逆迁移、法律/隐私选择或显著不可预估成本。

步骤、阶段、工具、模型、review 与中间 checkpoint 可按新证据合并、跳过、重排或替换。硬的是 acceptance criteria、traceability、evidence integrity 与边界，不是 recipe 的形状；reviewer 只能报告具体 failure mode，不能用 taste-only 要求移动冻结 contract。

模型绑定的 correction/re-review 只有在任务证据能确认 matching live package、role 与 actual model 时才复用 agent；否则 fresh-spawn 显式 typed role。advisory routing 可提示 `resume_agent` 的 auditability 不足但不硬阻断，显式 strict profile 可拒绝。复用或 role/model 改变不重置适用 budget；一旦 evidence 表明 mismatch，就记为 routing violation，不得用错配角色完成验收。

按不确定性类型路由，而不是只看任务标签。若 Terra 主控及 Luna/Terra 子任务持续在同一核心算法、系统架构或研究执行不变量上枚举近似方案，却没有形成可证伪不变量、判别实验或工件，继续增加同质 token 不算进展。此时优先提出一次紧凑的 `sol_architect` 问题，要求返回具体构造、反例、tradeoff 或 proof obligation；随后主控必须选择可测试路径，或诚实标为 `[UNCERTAIN]` 停止。已有 oracle 或 Terra 正在收敛时不得把 Sol 变成固定阶段，也不得用固定分钟数代替进展判断。

委派必须尊重 critical path。若核心不变量或架构尚未确定并阻断实现，不要提前让 Luna 重新发明架构，也不要让普通 reviewer 在没有工件时做同质搜索；先由主控、判别 oracle 或一次紧凑 architect 关闭该不确定性，再把稳定构造和客观验收交给 Luna。pre-implementation review 只有在问题被写成具体 hypothesis/failure mode 时才有价值。并行的是稳定 sidecar，不是多个 agent 争用同一个未知。

子任务使用能保真的最小自包含上下文：优先 `fork_context=false` 或平台支持的最小 history，并在 compact packet 中给出 objective、scope、当前 artifact/evidence、acceptance 与 stop condition。仓库工件通常比继承多个长 turn 更便宜、更可审计；只有无法压缩的具体依赖才能正当化更多 inherited context。

## 开发 v1 的 canonical mapping

- v1 的完整目录树、十步 scaffold、`REQUIREMENTS.md`、`NON_GOALS.md`、`ARCHITECTURE.md`、ADR、RUN/PITCH 与 tests 分层是长期 product 的参考结构，不是所有开发任务的预施工清单。小型任务可用请求、issue、计划或测试中的 compact contract；中大型项目只持久化生命周期确实需要的稳定事实。
- “spec gate”约束的是目标、non-goals、范围与验收在语义上足够明确，不是指定文件必须存在。public contract 只在新增或改变 public API/协议/兼容承诺时适用；ADR 只记录影响未来工作的持久决策。
- drift-check 在可信 scope-creep 风险、integration、handoff 或 delivery 边界执行，可并入 diff review；不要求每 commit 生成需求映射表。额外防御只有在具体失败路径、比例化成本和无新增语义同时成立时放行，“以后也许有用”的抽象、gate、测试或文档应删除。
- acceptance、full suite、dependency/security/performance scanner 与 independent review 均由实际 claim、影响面和风险触发，不因 v1 表格出现而自动启用。能在当前 session 完成或由 Git/issue/PR 恢复的任务不创建 durable state；真实跨 session/交接风险才复用一个轻量载体。

## Gates 与环境参数

所有 ContestOS 项目的共同完成标准是 claim/contract↔evidence closure 与 no overclaim。reproduction、contamination、statistics、performance、security、human review 等检查仅在对应 claim 或风险触发时启用；未触发的检查不必逐项登记 `not applicable`。

Review 可使用 `REVIEW_PROFILE=ordinary|api|security|architecture/data` 限定范围。API correctness 需要 Sol risk judgment 时，不自动升级为完整 security workflow；完整 codex-security workflow 只在具体 adversarial security trigger 存在时适用。Skill 是正交 adapter，不能扩大冻结 acceptance、stage 或 artifact；达到 verdict 所需证据即停止，非阻断项进入 backlog 或标为 `[UNCERTAIN]`，尤其是 pre-scale research hardening。

在新 project directory 首次 write、stage 或 commit 前，先用 `git rev-parse --show-toplevel` 确认 root；若目录应独立，使用独立 `git init` 或 worktree。一次只运行一个 full suite；重跑前仅检查/关闭自己此前的 process/session。只有下一步依赖尚未完成的 package 时才做一次与其复杂度相称的 bounded wait，避免短 polling、重复 raw transcript 读取，并把实际 monitoring WCU 计入成本记录。wait timeout 只表示“尚未完成”，不是负面 verdict；主控不得在所需子任务仍 open 时直接结束，除非明确取消并记录该 package 未完成。

环境与锁定器由项目生态注入，不得假定 Python 或 uv：使用 `{ENV_CMD}` 准备/验证环境，使用 `{LOCK_CMD}` 生成 `{LOCK_FILE}`，并用项目声明的 verify command 证明可复现。只有 Python/AI 项目选择 uv 时，`uv`/`uv.lock` 才是一个合适的参数实例；它不是 universal default。

## 启用与完成

项目级 `AGENTS.md` 同时引用所选 `contestos-*-v1.md`、本 overlay 与 Supervisor。完成时优先报告结果和决定性证据；实际发生且影响交付的 fallback、HUMAN/re-contract、风险检查、限制与 Git 状态才补充，不按模板列空项。上述优先级与硬锚优先于 v1 中冲突的运行时措辞。
