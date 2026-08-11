# Skill / MCP adapters（SOP 增强层）

> 本文件不是第二套路由器。任务先按 `README.md` 选择骨架与 SOP，再按需选择 Skill 或 MCP 适配器。它们不能替代 P1–P4、SOP 门禁、独立 oracle 或 HUMAN gate。

更新时间：2026-08-11

## 统一调用契约

```text
任务 → agent-sop 任务分类 → skeleton / SOP →（按需）Skill / MCP adapter → 证据 → SOP gate
```

## SOP 与 Skill 的正交边界

- SOP 负责 outcome contract、授权/风险边界、evidence quality、停止与 re-contract 规则，以及交付真相；不负责领域技术或工具实现。
- Skill 是 capability adapter：提供领域方法、工具操作、artifact format 或 specialized oracle。它可以在已选 SOP 外直接按需使用，但不能改变授权、路由政策、成功标准、claim、HUMAN 边界或制造 mandatory stage。
- Skill 指令服从 user、project 和 SOP authority。它只能在指出与冻结 claim 相关的具体失败路径后，建议额外检查。
- Skill 是 optional、replaceable capability；安装更多 Skill 不是质量证据。Skill 的 presence、version 或 hash 不构成通常的完成门禁。

- Skill 只负责领域知识、文件格式和工具操作；完成判定仍由 SOP 负责。
- MCP 只负责受控的外部数据或动作能力；不能自行决定任务分类、授权范围、失败策略或完成状态。
- Skill 产生的事实、数字、引用和图表必须进入项目规定的 ledger、manifest、results 或交付物目录。
- 失败、缺证据、缺依赖和外部服务不可用时按 P3 失败；不得静默换数据、换模型、换搜索源或生成占位结果。
- 远程、凭据、外发数据和发布动作仍受对应 SOP 与 HUMAN gate 控制。

## MCP 的位置

MCP 是能力层，不是流程层。调用前必须已经有：任务契约、允许的数据范围、工具用途、失败处理和回写产物。MCP 返回的数据仍需经过独立核验；MCP 执行的写入、发布、提交、消息发送或远程操作仍需命中对应 SOP 的授权和 HUMAN gate。

## 选择纪律（不是新门禁）

- 先由 SOP 冻结任务类型、结果契约与验收，再从已覆盖的能力槽中选择**最小充分集合**；不能因为某个 Skill 已安装就触发它。
- 能力缺口由可观察证据触发，例如缺少视觉目标、真实数据比较、键盘/浏览器证据、方法到代码的 fidelity 证据、性质测试或平台 profiler 解释；不得让实现者用“我觉得我会/不会”自判。
- 同一角色槽位默认单选。多个 Author 应隔离产出候选后再比较；Author、Implementer、Reviewer、oracle executor 可按真实失败路径跨角色组合，但不形成固定流水线。
- 下文的 `explicit-only`、`conditional`、`reference/hold` 与 `reject` 是选型结论，不是新的完成状态机。单一 fixture 或 Skill presence/version/hash 均不能成为通常门禁。
- 候选评测的 fixture、截图、缓存和盲审产物留在独立实验目录；本仓库只保留稳定的适配边界与来源，避免把评测台变成第二套 SOP。

## 已安装适配器（固定来源不等于已验证）

### 目标与开发

| Skill | 适配 SOP | 用途 | 约束 |
|---|---|---|---|
| `define-goal`（OpenAI） | `autonomous-supervisor`、`write-contract` | 把模糊意图变成可测目标、证据和范围 | 只定义目标，不创建执行台账或替代项目契约 |
| `web-design-guidelines`（Vercel） | `write-contract`、`drift-check` | UI、可访问性和 Web Interface Guidelines 审查 | 只作 UI oracle，不替代功能验收 |
| `composition-patterns`（Vercel） | `write-contract`、`drift-check` | React 组件边界、组合模式和长期可维护性 | 只在 React/组件架构任务触发 |

### AI 顶会科研：批准 proposal 的执行

默认输入是用户已经批准的 AI proposal。Agent 的责任是忠实实现方法，正确且高效地运行有判别力的实验，并交付可复现、可审计、足以支撑实际 claim 的证据。除非用户明确要求 proposal admission、idea generation、collision review 或论文交付，不重新选题，也不默认触发泛文献综述、泛写作或完整科研生命周期。

| 能力槽 | Skill | 触发与产物 | 当前处置 |
|---|---|---|---|
| 默认执行入口 | `research-execution-grill`（本仓库） | 把批准的 claim 转成实现/实验契约、主要 failure mode、oracle、预算、最小 pilot、kill/scale criteria 和下一可执行步骤 | `default`；不生成 idea，不替换 proposal |
| claim-to-test Reviewer | `hypothesis-generation` | 已批准 claim 缺少 rival explanation、可证伪预测、negative control 或 indeterminate outcome | `conditional challenger`；只使用窄子集，不生成新方向或宣布 novelty |
| 数据与预处理 Reviewer | `exploratory-data-analysis` | 数据来源、split、预处理、缺失、泄漏或异常可能改变结论 | `conditional challenger`；只报告有因果关系的风险，不自动清洗或改数据 |
| 科学有效性 Reviewer | `scientific-critical-thinking` | 已有具体的偏差、混杂、替代解释或 claim 越界失败路径 | `conditional challenger`、默认 report-only；不能自建新 gate |
| 通用方法参考 | `experimental-design`、`statistical-analysis` | 需要传统随机化/阻断/DOE 或通用检验选择时 | `reference/hold`；其生物/临床/经典统计默认不能替代 AI 实验设计或 AI statistics oracle |
| 论文交付旁路 | `scientific-visualization`、`scientific-writing` | 用户明确进入图表、论文或投稿交付 | `explicit-only`；不参与默认实现和实验执行 |
| proposal 上游旁路 | `scientific-brainstorming`、`literature-review` | 用户明确要求 idea generation、proposal admission 或顶会 collision review | `explicit-only`；输出不是已验证的新颖性或实验结论 |

K-Dense 子集经过源码、脚本和固定版本审阅，但其单元测试主要验证 bundled helpers，不证明 Agent 能更好地完成 AI 顶会 proposal。除 `research-execution-grill` 外，不把安装状态写成稳定质量结论；候选需在冻结 gold、无 Skill 基线和独立盲审下证明净提升。

### 外部搜索的本机治理覆盖

`literature-review` 只在显式上游任务中使用；其默认推荐的 `parallel-cli` 和可选 OpenRouter 图示脚本不获得运行权。当前工作站规则覆盖这些默认值：

1. 先用本地 SearXNG、已配置 Zotero 和受治理的论文工具。
2. 外部搜索或 API 只有在对应 SOP 明确允许时才启用，并记录查询、日期、来源和凭据边界。
3. 未发表、敏感、私有、受控或个人数据不得送入外部搜索、模型或图示服务。
4. OpenRouter 图示脚本默认不调用；缺少凭据必须失败，不得自动换提供商。

## 受控候选（未自动安装）

这些候选只在命中对应证据时显式调用。`reference/hold` 表示候选本身有价值，但现有对照尚未证明相对强基线有稳定净提升。

### 项目开发：Product UI 与 Marketing

| Profile / 槽位 | 候选 | 触发证据 | 负触发与边界 |
|---|---|---|---|
| Product UI / Visual Author | OpenAI Product Design `ideate`；Anthropic `frontend-design` 仅作隔离对照 | 用户要求产品级视觉质量，但 brief 尚无桌面/移动视觉目标，或现有结果明显通用化 | 不用于 backend-only、小 UI bug、已有精确 Figma/设计系统的照图实现；同槽 Author 不串联 |
| Product UI / data-viz | `visualization-strategy-and-critique` | 存在真实多变量数据和明确比较问题 | 不得虚构时间序列、阈值、告警、实时遥测或因果解释 |
| Product UI / Implementer | 中性实现者；有冻结 mock 时可对照 `image-to-code` | 已选视觉目标需要落到当前工程栈 | 不得另起视觉方向、扩大产品范围或自行宣布 fidelity/pass |
| Product UI / Reviewer | `improve-ui`；主方向成立后可用 `make-interfaces-feel-better` quick | 截图/运行态暴露层级、密度、响应式、hit area、排版或 motion 的具体失败路径 | 默认 report-only；没有高置信 finding 时停止，不能用品味扩大 acceptance |
| Marketing / Author→Implementer | Taste `imagegen-frontend-web` → `image-to-code` | landing、portfolio 或品牌营销页，素材与 art direction 属于交付质量 | 不用于 dashboard、后台工具或普通 preserve-brand 小改动；生成图片中的文字/数字不是事实来源 |
| Browser oracle executor | 固定版本 browser executor + axe | contract 要求真实交互、响应式、键盘、console/request 或 a11y 证据 | flow 与 pass/fail 由 SOP 提供；工具不能自修复后自证完成 |

营销页需要展示产品时，应消费 Product UI Profile 已验证的真实截图或工件，不能让 Marketing Author 虚构产品界面。正常依赖、字体、图标、chart primitive 与图片资产是否允许，继续由项目契约和 `add-dependency` 决定。

### 项目开发：正确性、安全与性能

| 候选 | 角色与触发 | 当前处置 |
|---|---|---|
| Vercel `react-best-practices` | React/Next 多组件实现后的性能与实现质量 Reviewer | `conditional`；不解决 taste，不在非 React 项目触发 |
| Trail of Bits property-based testing / libFuzzer | roundtrip、inverse、idempotence、parser、codec 或 protocol 的 Author/Reviewer | PBT 为 `reference/hold`；fuzz 按语言和真实输入面条件测试，依赖/时长需授权 |
| GitHub Actions hardening | workflow diff 出现 untrusted metadata、token、runner trust 或 mutable action ref | `reference/hold`；安全 finding 仍需独立 validation |
| Addy accessibility | UI 已实现且需要源码/截图层面的 a11y Reviewer | `conditional challenger`；最终由 axe、keyboard、focus、contrast 实证判定 |
| Grafana k6 | 有明确性能目标和允许施压的目标时生成负载脚本 | `conditional challenger`；脚本生成与实际打目标分开授权，默认只打本地 fixture |

### AI 顶会科研：待验证能力槽

以下是当前真实能力缺口，不是新增强制阶段；只有具体 proposal 暴露对应失败路径时才选用。

| 能力槽 | 候选方向 | 触发证据 | 当前处置 |
|---|---|---|---|
| Method fidelity Reviewer | 待选型/自建的窄 Skill | equation、pseudocode、loss、gradient、mask、状态更新、trajectory/reward/credit assignment 或 silent fallback 可能与实现不一致 | `priority-1 reference/hold`；Grill 已要求最小语义→代码→oracle mapping，候选仍须用 tiny deterministic fixture 与独立 differential/property oracle 证明额外净提升 |
| AI experiment-design Reviewer | 待选型/自建的窄 Skill；K-Dense `experimental-design` 仅作参考 | baseline parity、ablation、negative control、seed、调参预算、holdout、judge 或 pilot→scale 设计可能不足 | `priority-2 reference/hold`；必须面向 AI benchmark 与机制 claim，不能机械移植传统 DOE |
| AI evaluation executor | ModelScope EvalScope 或项目原生 harness | 项目明确使用 LLM/VLM/Agent benchmark、API endpoint 或推理性能测量 | `conditional challenger`；只执行固定 benchmark/config，不能决定数据、baseline、contamination、claim 或完成状态 |
| AI statistics oracle | 待选型/自建的窄分析适配器 + 现有 `statistics-oracle` | 即将基于多 seed、样本、task、benchmark、judge 或失败/timeout 作比较性结论 | `priority-3 reference/hold`；需要 paired/hierarchical uncertainty 与 multiplicity，通用统计 Skill 不自动获得 oracle 独立性 |
| 栈专用 Implementer | 项目已选 HF/TRL、verl、Ray、NeMo 或其他训练栈后的窄 Skill | 仓库和 proposal 已明确使用该栈且原生文档/测试仍有能力缺口 | `discovery-only`；不得自动提交付费训练、上传 Hub、启用外部跟踪或改变用户的 scale 决定 |

benchmark 污染、环境/结果复现、claim、holdout、预算和 scale 继续由现有 `contamination-check`、`lock-env`、`reproduce-result`、`run-experiment`、`statistics-oracle` 与 Research Grill 控制。外部 Skill 只能补领域方法或执行器，不能复制控制面。

### 竞赛与黑客松：赛制专用能力

`run-competition` 先冻结判定、反馈、工件、环境、事件和外部动作包络；下列 adapter 只填充命中的能力槽。一个比赛可以组合多行，例如产品型 agent 黑客松同时需要官方 SDK/MCP、真实部署/browser evidence、演示材料和受控外部提交。

| 能力槽 | 候选 / executor | 触发与边界 |
|---|---|---|
| 算法 / output / interactive correctness | 官方编译器、checker、local judge；differential/PBT/fuzz | 按输入/协议的可信失败路径启用；PBT/fuzz 不是每题固定阶段，interactive 需覆盖 timeout、flush、协议顺序等实际风险 |
| Kernel / 系统性能 | 官方 benchmark；NVIDIA nsys/ncu、ROCm、Ascend、Triton、CPU 平台工具 | 先用同口径 benchmark 建基线；只有瓶颈/机制仍不确定时 profile，不自动 sudo、sysctl、CAP_SYS_ADMIN 或弱化隔离 |
| 窄性能实现 | CUDA Graph 等平台专用 Implementer | 只有测量已指向相应瓶颈且契约允许修改路径时启用；实现后用同一 workload 与正确性语义复测 |
| 数据 / leaderboard | 官方 Kaggle CLI 或平台 API/CLI | 只执行 dataset、kernel、submission 等已授权平台命令；split、holdout、泄漏、public/private gap、submission budget、final reserve 与是否提交归 SOP |
| agent / hidden runtime | 官方 harness、container、verifier、trajectory/trace executor | 复用比赛的 interface、token/time/network/sandbox 与 injected verifier；不自建第二 judge，不因 timeout 丢弃本可保留的 checkpoint/partial output |
| 产品型黑客松 | 比赛强制的 SDK/API/MCP/partner tech；browser/deploy oracle；按需的 notebook、deck、video 或文档 adapter | adapter 证明真实集成、运行路径和交付格式；不能替代 rubric、资格、业务事实或演示真实性，也不能为使用某 Skill 而虚构 partner-tech 价值 |
| 论文到 notebook / 研究工件 | 官方 notebook runtime、paper implementation 工具与 evaluator | 验证方法 fidelity、可执行性、输出格式和资源限制；研究 claim 需要的复现/统计证据仍由科研 SOP 控制 |
| 外部提交面 | GitHub/Kaggle/Devpost/竞赛平台 connector、CLI 或 browser executor | 只在已冻结的平台、账户、次数/费用、final reserve、数据与公开范围内执行；保存 receipt/ID，不能自行接受条款、组队、公开发布或扩大预算 |

### `find-skills` 的位置

`find-skills` 只用于显式 discovery escalation：当冻结验收暴露未覆盖能力槽，且现有已批准适配器无法处理时，返回候选的 source commit、license、角色、触发/负触发、副作用、authority exclusions 与独立 oracle。它不得自动安装、激活、写入“已安装”列表、改变 acceptance 或决定完成；候选必须先在仓库外做静态审阅和真实对照。

## 版本与来源

安装时固定了来源 commit，便于 P4 追溯：

- OpenAI `define-goal`: `openai/skills@49f948faa9258a0c61caceaf225e179651397431`
- Vercel `web-design-guidelines`、`composition-patterns`: `vercel-labs/agent-skills@7c180d9044c9ae2b442b567aad4e42a28dd5ed62`
- K-Dense 科研子集：`K-Dense-AI/scientific-agent-skills@d767725c6e93b1d02a220e6be75b261a9833ede5`

以下是候选评测时使用的固定来源，不表示已经安装或获得运行权：

- Taste：`Leonxlnx/taste-skill@e988add20dab0fa97d7a76781c48961c8184288e`
- OpenAI Product Design：`openai/role-specific-plugins@fe5608d2512a7d6a7b9821ce8a88c48464ecd6e4`
- OpenAI data visualization：`openai/plugins@11c74d6ba24d3a6d48f54a194cd00ef3beea18f9`
- Product UI Reviewer：`ibelick/ui-skills@fdc667270fd2c71b3a8b7aca04dda154a7b8a5d5`
- Interface polish：`jakubkrehel/make-interfaces-feel-better@5f3c3c26c512b3469e6dbcab8a0d73e8b575a566`
- Anthropic frontend-design：`anthropics/skills@f17010c9bb483898c1d9c9f42dde2b3a98889434`
- Trail of Bits testing：`trailofbits/skills@7b9bd5f950f89a9ba71b249b9801c1a95be3928e`
- Addy accessibility：`addyosmani/web-quality-skills@95d6e255afe1596b557d7a8498517884438f5b3a`
- Grafana k6：`grafana/skills@d9dfb9ec7a6b1ac6c8ec9741ec045ad6f412dec6`
- GitHub Actions hardening：`github/awesome-copilot@3f0bba475ec40b9680e1d0311b9caffeec5ad4c3`
- ModelScope EvalScope：`modelscope/evalscope@e82fd3845d18ae5379edd33136dae9342f6875a3`
- NVIDIA profiling：`NVIDIA/TensorRT-LLM@10689401f113efb1212c51943a5a239d5d21345f`

K-Dense 是维护较好的通用科学 Skill 库，不是 OpenAI 官方 Skill，也不是已验证的 AI 顶会实验执行系统。具体研究结论仍须经过本地数据、独立 oracle、复现和人工审查。

## 不采用的替代方案

- 不安装新的 Superpowers 全局流程包：它的 brainstorming、planning、TDD、review、subagent workflow 与现有 SOP 重叠，会增加上下文和路由竞争。
- `addyosmani/agent-skills` 可作为开发流程设计的参考，但暂不启用为第二路由器；已有 SOP + Vercel/GitHub 专项 Skill 足够覆盖当前开发门禁。
- 不安装泛化的 Kaggle、自动刷榜或“AI research autopilot”包；比赛的 correctness/evaluation evidence、按需 local proxy、泄漏边界、submission budget/final reserve、外部授权和 fallback 语义必须由 ContestOS/SOP 控制，adapter 不得形成第二个刷榜状态机。
- 不把 Impeccable 完整 umbrella、Taste `redesign-existing-projects` 或其他自带 router、持久上下文、hooks、评分/修复循环的包作为全局 Skill；只允许经验证的窄命令或角色。
- 不采用由 browser 工具自行触发、自行修复并自行宣布通过的 verification wrapper；可复用底层浏览能力，但 route、flow 与 verdict 必须来自 SOP。
- 不采用要求自动提交付费训练、强制上传模型/数据或强制启用外部跟踪的训练 Skill；只允许从中抽取经验证的栈知识，并由现有预算与远程动作边界控制执行。
- 不允许运行时动态 `find-skills` 自由搜索、安装和组合；这只适合隔离探索，不属于稳定交付路径。
