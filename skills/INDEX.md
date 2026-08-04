# Skills 清单

来源:`~/ops/claude/skills/`(唯一事实源)。本文件只做索引,不镜像源码。新增/删除 skill 后同步更新本表。

## 研究类

| Skill | 用途 | 触发场景 |
|---|---|---|
| `deep-research` | 13-agent 通用深度研究流水线;7 种模式(完整研究/快速简报/论文审阅/文献综述/事实核查/苏格拉底对话/系统综述+meta 分析) | research、深度研究、文献综述、systematic review、fact-check、引导式研究、研究方向等 |
| `brainstorm` | 生成并打磨研究/工程想法,压缩成可测试候选 | 想点子、方向不明、候选想法打磨 |
| `map-build` | 为子领域构建概念图:聚类、空白、潜在竞争者 | 建领域地图、摸清子领域结构 |
| `gap-finder` | 分析领域地图/综述,找出值得验证的高价值未探索空白 | 找研究空白、gap 分析 |
| `survey` | 把限定范围的文献综述综合为主题、代表工作、分歧与研究方向 | 写综述、领域总结 |
| `paper-read` | 把论文提炼为:主张、证据、弱点、后续问题 | 精读论文、论文拆解 |
| `red-team` | 模拟强审稿人反对意见,压力测试想法/计划/论文草稿 | 红队、对抗审查、投稿前自查 |
| `arxiv-tracker` | 跟踪限定领域的新相关论文,返回带重要性的排名摘要 | 追新论文、领域动态 |

## 学术写作类

| Skill | 用途 | 触发场景 |
|---|---|---|
| `academic-paper` | 12-agent 论文写作流水线;10 种模式(全文/计划/大纲/修订/修订教练/摘要/文献综述/格式转换/引用核查/披露),6 种论文类型,LaTeX/DOCX/PDF 输出 | 写论文、学术论文、AI disclosure、審查意見等 |
| `academic-paper-reviewer` | 多视角论文审稿:模拟 5 位独立审稿人(EIC + 3 同行 + 魔鬼代言人),支持全文审、复审、快速评估、方法论聚焦、苏格拉底引导、校准模式 | review paper、peer review、审稿、calibrate reviewer |
| `academic-pipeline` | 研究 → 写作 → 完整性核查 → 审稿 → 修订 → 终稿的全流程编排(10 阶段,强制完整性验证与两轮同行评审) | academic pipeline、research to paper、完整论文工作流 |

## 信息采集与监控类

| Skill | 用途 | 触发场景 |
|---|---|---|
| `x-monitor` | 监控 X/Twitter 上研究者、实验室与讨论,提取信号而非噪音 | 推特监控、学术动态、研究者动态 |
| `news-digest` | 聚合可及的公开 AI 新闻与社区信号,蒸馏出真正重要的内容 | AI 新闻摘要、每日动态 |
| `scrape` | 用本地浏览器与爬虫工具执行治理化网页采集,返回结构化、可归因输出 | 网页采集、数据收集(遵守 robots/限速) |

## 工具集成类

| Skill | 用途 | 触发场景 |
|---|---|---|
| `obsidian-skills` | Obsidian 集成 bundle(kepano,第三方,agentskills.io 规范):`defuddle`/`json-canvas`/`obsidian-bases`/`obsidian-cli`/`obsidian-markdown` 5 个子技能 | Obsidian 笔记操作、canvas、markdown 处理 |

## 按工作流使用

- **完整学术流水线**:`academic-pipeline`(编排)→ `deep-research`(研究)→ `academic-paper`(写作)→ `academic-paper-reviewer`(审稿)。
- **领域探索**:`map-build` → `gap-finder` → `brainstorm` → `red-team`。
- **持续追踪**:`arxiv-tracker` + `x-monitor` + `news-digest`。
