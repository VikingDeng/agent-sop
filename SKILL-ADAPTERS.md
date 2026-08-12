# Skill / MCP capability registry

> 本文件只定义能力层的边界、准入和证据要求，不分类任务、不选择模型/角色、不规定阶段顺序，也不改变任何 SOP 的验收与授权。候选、来源和状态的唯一登记表是 [`skill-registry.yaml`](skill-registry.yaml)。该文件采用严格 JSON 语法（JSON 是 YAML 1.2 子集），可直接用 Python 标准库 `json` 读取，不依赖 YAML parser。

更新时间：2026-08-12

## 1. 正交边界

```text
用户 / 项目契约
  → SOP Kernel：outcome、non-goals、授权/风险、claim↔evidence、停止/re-contract、交付真相
  → Domain Profile：同类任务特有的不变式
  → Capability slot：当前结果缺少的可观察能力
  → Skill / MCP / native tool：可替换的能力实现
  → Oracle evidence：回到原契约判定，不由能力实现自证
```

- **SOP** 决定什么算完成、什么需要授权、什么证据足以支持 claim。它不因某个 Skill 存在而新增固定阶段。
- **Skill** 只补充专门知识、确定性工具操作、artifact 格式或窄 oracle。它不能改写 acceptance、claim、HUMAN 边界、预算、模型路由或失败语义。
- **MCP** 只提供受控的外部读取或动作能力。数据范围、写入/发布权限、凭据、费用和回写产物仍由原契约与对应 SOP 管理。
- **Oracle** 给出与 claim 匹配的真实证据。Skill 作者、实现者或 MCP 返回值不能仅凭自己的 verdict 宣布完成。
- **Codex adapter** 管理模型、sub-agent、Hook、WCU 和会话实现；这些不是 Skill registry 的字段或选择依据。

能力缺口必须由可观察失败路径触发，例如：没有真实浏览器交互证据、方法公式与实现无法 differential、性能瓶颈尚未测量、平台格式只能由官方 checker 判定。实现者的“我会做”或“我需要更多 Skill”都不是证据。

没有合格 Skill 时，Agent 继续使用原生能力、项目工具和最便宜的 discriminating oracle。**Skill 缺失本身不是项目 blocker，也不能降低验收。**

## 2. Registry 只登记能力，不进行任务路由

[`skill-registry.yaml`](skill-registry.yaml) 每条记录必须有下列可机读字段；`declared` 阶段未知值可以是 `null`，但必须附 blocker，不能伪装成已审计事实：

- `id`、`kind`、`capability_slot` 与可检验的 `value_claim`；
- 生命周期事实：`declared / audited / installed / enabled / evaluated / promoted`；
- repository、commit、subpath、content SHA-256、license evidence；进入 `audited` 前这些来源字段必须 exact 且非空；
- runtime/service/credential dependencies 和所有已知 side effects；
- positive trigger、negative trigger、non-goals 与 authority exclusions；
- 固定基线、fixture、重复次数、盲评、质量/成本/副作用指标、阈值、结果和失效日期。

Registry 明确不保存：任务类型到 Skill 的自动映射、Sol/Terra/Luna 选择、Agent 角色链、下一阶段、completion verdict 或强制调用次数。项目可以按当前 failure path 查询 `capability_slot`，但不能把 registry 反向当成第二套工作流。

### 生命周期语义

| 状态 | 可验证含义 | 不意味着 |
|---|---|---|
| `declared` | 已记录候选及预期增益 | 源码可信、可安装或有质量提升 |
| `audited` | exact bytes、license、依赖、副作用和权限排除已静态核验 | 相对强模型有净提升 |
| `installed` | 审计过的 digest 确实存在于目标环境 | 自动启用或稳定质量 |
| `enabled` | 在明确 activation policy 下允许被调用 | 每个匹配任务都应调用 |
| `evaluated` | 已完成登记的对照实验并保存原始证据 | 已达到 promotion 阈值 |
| `promoted` | 在当前模型、版本、fixture 与期限内证明净提升 | 永久有效或可以改变 SOP |

这些是候选状态事实，不是项目阶段。正常新增候选必须按上表前向推进；若导入历史安装，必须明确记录例外，且不得越级成为 `audited` 或 `promoted`。任何 source bytes、依赖边界、主要模型/Codex 能力或 fixture 分布发生 material change，均把 `promoted` 降回 `evaluated=false`，重新对照。

只有 `promoted=true` 且未过期的窄能力可以进入默认候选集；`evaluated` 但未晋级的能力仅供显式实验；其余候选不得在稳定运行路径自动安装或启用。

## 3. 相对于 GPT-5.6 的净增益测试

每个候选至少使用相同模型、effort、工具权限、项目 checkpoint、任务输入和预算比较三臂：

1. **Strong no-Skill baseline**：GPT-5.6 使用项目原生工具与完整任务上下文；不能故意弱化 prompt。
2. **Minimal reminder**：只给出候选最核心的一两条提醒，不加载完整 Skill。
3. **Full Skill**：加载固定 digest 的完整 Skill，记录实际触发和上下文成本。

第二臂用来区分“模型只是忘了提醒”与“Skill 真正提供了模型没有的能力”。只有 Full Skill 相对前两臂在盲评中产生稳定、可复现的净提升，才可能晋级。

评测必须与能力槽匹配：

- UI Author/Reviewer：同 brief、真实数据、相同素材预算，盲评运行态截图与关键交互；同时检查 responsive、a11y、console/request 和功能回归。
- Code Reviewer：植入已知缺陷并测 precision/recall、误报、scope 扩张和修复回归，不能只比较文字建议数量。
- Method/Statistics Reviewer：使用有 gold mapping 或已知统计陷阱的 AI 实验 fixture，测关键错误发现率与错误建议率。
- Tool executor：比较真实执行成功率、artifact 有效性、幂等/恢复、权限越界和未披露副作用。

共同记录 task success、gold-defect recall/precision、独立质量分、原验收回归、trigger precision、token/context/WCU、wall time、外部费用和副作用。阈值必须在看结果前填入 registry；单个宣传案例、单次截图、star 数、作者声誉、安装成功或 Skill 自评都不能作为 promotion 证据。

## 4. 默认选型政策

- 优先评测**外部开源、窄范围、版本可固定、输出可由真实 oracle 核验**的能力，而不是再写本地 prompt 包装器。
- 官方 checker/compiler/browser/axe/profiler/benchmark/platform CLI 等工具型适配器优先，因为其增益和输出通常更可判定；具体项目工具只有形成可复用、固定来源的 adapter 时才登记为 Skill。
- 纯文本的 goal decomposition、brainstorming、planning、TDD、generic review、critical thinking、scientific writing 等能力，默认视为 GPT-5.6 已具备。没有三臂对照的显著增益时保持 `reject/hold`，不得默认启用。
- umbrella router、autopilot、持久上下文、自动评分修复循环或自带 sub-agent workflow 的包不得作为全局 Skill；若其中确有价值，只能抽取可单测的窄能力重新审计。
- 同一能力槽可以保留多个实验候选，但稳定调用一次只选一个。若要比较多个 Author，必须隔离生成并盲选，不能串联造成无法归因的“Skill soup”。
- Skill/MCP 的事实、数字、引用、图表和外部 receipt 必须写回项目规定的证据载体；缺依赖、缺凭据或服务失败时诚实失败，不自动换来源、数据、模型或服务商。

### Catalog、安装与激活不是一回事

“local Skill”只表示它位于 Codex 会扫描的本机目录，不表示它是本地作者编写，也不构成质量结论。稳定治理必须区分：

1. **离线 catalog**：来自官方、maintainer 或社区仓库的发现记录，不进入运行时 prompt；
2. **audited candidate**：exact source、commit/subpath/hash、license、依赖、副作用和边界已经核验，但仍不代表有净增益；
3. **installed / enabled**：固定字节存在于目标环境，且只在明确 activation policy 下可调用；
4. **promoted**：相对当前强模型和 minimal reminder 已经用登记的 fixture 证明净提升，才可进入小型隐式激活集。

优先使用 OpenAI bundled/curated plugin 或原维护者发布的开源 Skill；“官方”“开源”“star 多”和“已安装”都不能跳过 exact-source 审计与行为评测。技术栈、产品平台和高副作用 Skill 默认放在项目/插件层，不复制为用户级常驻副本。若同名 Skill 同时由用户目录和插件提供，只保留一个预期来源；Codex 不会合并同名 Skill，重复项会造成选择歧义和上下文浪费。

备份、退役 shim 和历史快照不得留在 Skill discovery 目录中。Codex 会跟随 symlink；即使目录名带 `.backup-*`，其中的 `SKILL.md` 仍可能作为重复 Skill 被发现。恢复副本应放在不被扫描的专用备份目录。

Registry 描述的是稳定 runtime 的准入，不声称能关闭平台随 App/插件暴露的全部能力。平台内置或已安装插件可能按更高层的产品策略出现在当前会话；它们仍服从原契约与权限边界，不能因此被计为本 registry 的 `promoted`。实际激活面必须用 Codex 的 prompt/diagnostic 输出复核，而不能只看磁盘目录或 registry 自述。

### Research Grill wrapper 的退役状态

历史上的 `codex/skills/research-execution-grill` 只把本仓库科研 SOP 再包装给 Codex discovery。它没有独立工具、外部知识或相对于直接读取 SOP 的增益证据，因此：

- 不再称为默认科研 Skill，不计入能力覆盖或“已验证 Skill”；
- 科研实施直接以 `sop/tier1-skeleton/research-execution-grill.md` 为控制面；
- 该 wrapper 已从稳定 installer/runtime 退役，registry 只保留其历史 provenance，不计为 installed/enabled；
- 若平台将来确实需要 discovery 入口，应另建 explicit-only thin launcher，并先做“直接 SOP vs SOP+launcher”对照；它仍不能被计作领域能力。

## 5. MCP 与外部动作

MCP adapter 也使用同一来源、依赖、副作用、trigger 和 evaluation 字段，但服务可用不等于数据可信或动作获授权：

- 读取类 MCP 记录查询范围、时间、来源和缓存/新鲜度；高影响事实按 claim 风险交叉核验，而不是机械要求所有返回值双重验证。
- 写入、提交、发布、消息发送、付费调用和远程变更只能在原授权包络内执行，并保存 receipt/ID；MCP 不能自行扩大范围或接受新条款。
- 私有、未发表、受控、个人或敏感数据不得因 adapter 默认配置而外发。缺凭据必须失败，不得偷偷换 provider。

## 6. Discovery 与 `find-skills`

稳定运行路径**禁止运行时调用 `find-skills` 搜索、安装、组合或激活新 Skill**。动态 discovery 会引入未固定代码、未知 license/side effect、prompt injection 和无法归因的质量变化。

只有在单独的离线选型任务中，已冻结的 capability slot 确实没有候选时，才允许使用 `find-skills` 生成 `declared` 记录。此时未知来源字段保持 `null + blocker`；进入 `audited/installed` 前必须补齐 exact source、license、依赖、副作用、negative trigger 和评测计划。在隔离环境静态审阅和三臂对照前，不得安装到稳定 runtime。`find-skills` 不是让 Agent 自己判断能力缺口的机制，也不拥有任何项目完成权。

## 7. 当前候选结论

具体候选、exact source 与缺失审计项见 [`skill-registry.yaml`](skill-registry.yaml)，首轮审计/对照证据记录在 `skill-evaluations/round1-2026-08-12.md`。当前没有任何外部候选达到 `promoted`：

- 三个 Visual Author 已完成 exact-source 静态审计，但尚未完成运行态盲评；React、accessibility、workflow hardening、k6、EvalScope 和 NVIDIA profiling 仍处于不同程度的待审计/待对照状态；
- Trail of Bits property-based testing 已完成 3×3 非正式 pilot，完整 Skill 在初始 hidden-check 轴没有优势，盲评高于 baseline 但低于两句提醒；因随机化、持久 raw artifacts 和成本指标不完整，它仍是 audited 而非 evaluated，并保持 disabled/unpromoted；
- `define-goal`、K-Dense 泛化文本子集与内部 Grill wrapper 不默认启用；K-Dense 的四个科研候选经审计不匹配“已批准 AI proposal 的忠实实现”，仅保留一个 text-only DOE sentinel 的实验可能；
- `kdense-statistical-power` 已完成 exact-source 静态审计并进入 explicit-only pilot，但尚未完成相对 GPT-5.6 的三臂净增益评测，因此不能隐式触发或被称为“已验证增强”；
- method-fidelity、AI experiment design、更广义的 AI statistics 与具体 HF/TRL/verl/Ray/NeMo 栈仍是待选型能力槽，不用未经验证的通用科研 Skill 填空。

这一结论只说明 Skill 层尚未证明净增益，不降低 development、research 或 competition 的原验收，也不阻止 Agent 使用项目原生工具完成任务。
