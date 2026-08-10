# Skill / MCP adapters（SOP 增强层）

> 本文件不是第二套路由器。任务先按 `README.md` 选择骨架与 SOP，再按需选择 Skill 或 MCP 适配器。它们不能替代 P1–P4、SOP 门禁、独立 oracle 或 HUMAN gate。

更新时间：2026-08-07

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

## 已安装的精品适配器

### 目标与开发

| Skill | 适配 SOP | 用途 | 约束 |
|---|---|---|---|
| `define-goal`（OpenAI） | `autonomous-supervisor`、`write-contract` | 把模糊意图变成可测目标、证据和范围 | 只定义目标，不创建执行台账或替代项目契约 |
| `web-design-guidelines`（Vercel） | `write-contract`、`drift-check` | UI、可访问性和 Web Interface Guidelines 审查 | 只作 UI oracle，不替代功能验收 |
| `composition-patterns`（Vercel） | `write-contract`、`drift-check` | React 组件边界、组合模式和长期可维护性 | 只在 React/组件架构任务触发 |

### 科研

默认边界:用户提供的 proposal 视为已经批准的研究方向。除非用户明确要求 idea generation 或 proposal admission,科研适配从 `research-execution-grill` 开始,不重新发明或改写研究方向。

| Skill | 适配 SOP | 产物 / 门禁 |
|---|---|---|
| `research-execution-grill`（本仓库） | `research-execution-grill`、`run-experiment` | 把已批准 proposal 转成 blocked/ready 的实现与实验契约；不生成 idea |
| `scientific-brainstorming` | `research-investigation` | 仅在用户明确要求 idea generation 时使用；候选方向不作为证据 |
| `literature-review` | `research-investigation`、`fetch-assets` | 搜索边界、证据表、去重与引用核验 |
| `hypothesis-generation` | `research-execution-grill`、`build-oracle` | 仅补齐已批准 claim 的 rival hypothesis、可证伪预测与预注册分析,不得改题 |
| `experimental-design` | `run-experiment` | 实验设计、随机化/阻断、混杂控制 |
| `exploratory-data-analysis` | `run-experiment` | 有界数据质量、缺失、泄漏、异常和敏感性报告 |
| `statistical-analysis` | `statistics-oracle`、`reproduce-result` | 假设检查、效应量、不确定性和统计报告 |
| `scientific-critical-thinking` | `build-oracle`、`statistics-oracle` | 证据等级、偏差、混杂和论证漏洞审查 |
| `scientific-visualization` | `statistics-oracle`、`scientific-paper` | 保真、可访问、可复核的图表与图表 manifest |
| `scientific-writing` | `scientific-paper`、`reproduce-result` | claim–evidence ledger、引用、作者责任和一致性检查 |

### 外部搜索的本机治理覆盖

`literature-review` 上游默认推荐 `parallel-cli`，并包含可选的 OpenRouter 图示脚本。当前工作站规则覆盖这些默认值：

1. 先用本地 SearXNG、已配置 Zotero 和受治理的论文工具。
2. 外部搜索或 API 只有在对应 SOP 明确允许时才启用，并记录查询、日期、来源和凭据边界。
3. 未发表、敏感、私有、受控或个人数据不得送入外部搜索、模型或图示服务。
4. OpenRouter 图示脚本默认不调用；缺少凭据必须失败，不得自动换提供商。

## 版本与来源

安装时固定了来源 commit，便于 P4 追溯：

- OpenAI `define-goal`: `openai/skills@49f948faa9258a0c61caceaf225e179651397431`
- Vercel `web-design-guidelines`、`composition-patterns`: `vercel-labs/agent-skills@7c180d9044c9ae2b442b567aad4e42a28dd5ed62`
- K-Dense 科研子集：`K-Dense-AI/scientific-agent-skills@d767725c6e93b1d02a220e6be75b261a9833ede5`

K-Dense 是高质量的维护者/领域库，不是 OpenAI 官方 Skill；它的科研内容作为 SOP 的专业适配器使用，不能获得“官方 oracle”地位。具体研究结论仍须经过本地数据、独立 oracle、复现和人工审查。

## 不采用的替代方案

- 不安装新的 Superpowers 全局流程包：它的 brainstorming、planning、TDD、review、subagent workflow 与现有 SOP 重叠，会增加上下文和路由竞争。
- `addyosmani/agent-skills` 可作为开发流程设计的参考，但暂不启用为第二路由器；已有 SOP + Vercel/GitHub 专项 Skill 足够覆盖当前开发门禁。
- 不安装泛化的 Kaggle、自动刷榜或“AI research autopilot”包；比赛的 correctness gate、local proxy、submission ledger 和零 fallback 必须由 ContestOS/SOP 控制。
