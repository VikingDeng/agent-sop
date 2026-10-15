> **GitHub 公开快照说明**
>
> 本目录是 `/home/viking/dev/docs/_shared` 写作体系的公开快照，对应 **v1.0，冻结日期 2026-10-11**。
> 它是从本地维护源裁剪出来的只读参考，不在本仓库维护；改动写作体系请回到维护源，并按 `FREEZE.md` 登记。
>
> 其他 agent 接手写作任务时，按顺序先读这四份：
>
> | 顺序 | 文件 | 作用 |
> |---|---|---|
> | 1 | [`FREEZE.md`](FREEZE.md) | v1.0 的冻结范围、固定决策、唯一维护源清单与允许的变更 |
> | 2 | [`skills/research-writing-pipeline/SKILL.md`](skills/research-writing-pipeline/SKILL.md) | 中文技术文档的写作流程与判断标准 |
> | 3 | [`document-quality.md`](document-quality.md) | 交付检查口径：引用、图、表、公式、证据 |
> | 4 | [`agent-tasks/update-docs.md`](agent-tasks/update-docs.md) | 一句自然语言怎么调用、一轮做到什么程度、报告与问题状态表 |
>
> **发布裁剪**：模板源里缺失的 PDF 与压缩包（`*.pdf`、`*.zip`、`*.tar.gz`、`*.7z`）以及 `build/` 产物，
> 是发布时为大文件与生成物做的裁剪，**不是规则缺失**，也不代表模板不完整。
> 模板的规则与清单在 `paper-templates/templates.tsv` 与 `paper-templates/TEMPLATE_CATALOG.md`，两者完整保留。
>
> **路径说明**：下文按本地目录布局书写，`../AGENTS.md` 一类仓库外路径在本公开仓库中不存在；
> 目录内的相对路径（如 `paper-templates/templates.tsv`）按本目录解析。

# _shared — 文档共用基础

本目录是 `/home/viking/dev/docs` 下各项目共用**资产**的唯一真实来源。
改模板、改写作技能、改公共工具、改详细交付标准都在这里改；项目里放的是固定快照。
目录骨架、构建与基线规则在 [`../AGENTS.md`](../AGENTS.md)，不在本目录。

## 当前冻结版本

写作体系当前冻结为 **v1.0**（2026-10-11）：固定决策、唯一维护源清单、允许的变更与不引入项见
[`FREEZE.md`](FREEZE.md)。改动本目录写作相关文件前先读它，并按其中的变更记录要求登记。

## 资产清单

| 路径 | 是什么 | 谁在用 |
|---|---|---|
| `paper-templates/` | 本地模板库：`templates.tsv`（机器可读清单）、`TEMPLATE_CATALOG.md`（来源/官方还是社区/能否投稿）、`typst/`、`latex/`、`reports/`（自建模板）、`scripts/`、`shared/` | 所有 Typst / LaTeX 报告工程 |
| `skills/research-writing-pipeline/` | 中文技术文档写作流程与判断标准（`SKILL.md` 共用判断、信息与措辞；`references/document-genres.md` 文种入口：调研综述、工程技术文档、研究论文三类写法；`references/reader-examples.md`、`references/intro-analysis-protocol.md` 等按需参考） | Claude Code、Codex、dsh |
| `writing-exemplars/` | 技术文档范文库：`README.md`（选例与状态）、`INDEX.tsv`（12 条 13 列索引）、`principles.md`（7 条原则）、`macro-structure.md` / `micro-structure.md` / `boundary-cases.md`、`candidates/` | 改稿 agent、审阅者 |
| [`document-quality.md`](document-quality.md) | 详细交付标准（唯一来源）：**正文引用默认上标方括号 + 文末常规编号，官方要求优先**、参考文献与编号映射、图的交付物与图源、各类图的判断点、编号与引用、表格、公式与符号、证据、读者与页面、交付残留；每条标 `[机]` / `[审]` / `[待证]` | 改稿 agent、审阅者 |
| [`agent-tasks/update-docs.md`](agent-tasks/update-docs.md) | 日常任务口径：一句自然语言怎么调用、一轮做到什么程度、可改范围、报告与问题状态表 | 用户、执行 agent |
| `tools/compare_pdf.py` | 逐页 PDF 对比：页数 + 逐页文本 + 逐页 PPM 像素字节；只依赖标准库与 poppler-utils | `radar-data-gen`、`ai4ai` |

正式文档里的流程图、架构图、时序图、数据流图**只能是图片**：Mermaid、TikZ、draw.io、Graphviz
都只是可编辑源或生成工具，正文不展示 Mermaid 源码，须导出目标引擎实测能引入的图片（优先矢量）后由
`#figure` / `figure` 引入；Mermaid fenced block、ASCII 箭头、纯文字列表都不算图。完整口径
（含交付格式与分辨率、源与导出物的对应、交付前逐图核对、各类图看什么）见
[`document-quality.md`](document-quality.md) 第二、三节。

`tools/` 下只有 `compare_pdf.py` 这一个脚本，它是 `radar-data-gen/tools/compare_pdf.py`
与 `ai4ai/tools/compare_pdf.py` 的共同来源。迁入时三份内容相同，sha256 为：

```
8fedb5769e9dbb2021a9507a9d913d644f5e3fcf8c807400c4f9a0f0096e83f2
```

核对当前版本（同一版本应一致；项目固定旧版本时按其记录的哈希校验）：

```bash
sha256sum _shared/tools/compare_pdf.py \
          radar-data-gen/tools/compare_pdf.py \
          ai4ai/tools/compare_pdf.py
```

## 旧路径兼容链接

下面三条都指向本目录里的真实目录，仍可读；但维护性改动请直接改真实目录，
不要再经旧路径写入。

| 旧路径 | 指向 |
|---|---|
| `/home/viking/dev/projects/work/paper-templates` | `_shared/paper-templates` |
| `~/.claude/skills/research-writing-pipeline` | `_shared/skills/research-writing-pipeline` |
| `~/.codex/skills/research-writing-pipeline` | 同上 |

## 项目快照不会自动跟随

`radar-data-gen` 与 `ai4ai` 各自带一份 `tools/compare_pdf.py`；`radar-data-gen`
另有 `vendor/template/` 模板快照和 `template.lock` 校验哈希。这样项目不依赖
`_shared` 的绝对路径，能独立构建与交付。

代价是同步靠人：改了 `_shared` 的来源，项目副本不会跟着动。两个项目的 README
都记了来源路径与 sha256。与各自锁定版本不一致才是意外漂移，项目不必始终使用共享源的最新版。

### 升级模板（以 `radar-data-gen` 为例）

1. 先按 `AGENTS.md` 第 4 条保存变更前的 PDF，作为逐页对比基线；
2. 从 `_shared/paper-templates/reports/chinese-thesis-report/` 拷新版到 `vendor/template/`；
3. `make lock` 重新生成 `template.lock`（`make build` 不会自动改 lock）；
4. `make compare BASELINE=<第 1 步的旧稿>` 逐页对比。

`template.lock` 里的 `source` 字段是生成当时的路径记录。路径迁移后它可能仍是旧值：
校验只比对 `version` 与随附文件 sha256，不影响 `make lockcheck`。

### 升级公共工具

改完 `_shared/tools/compare_pdf.py`，只向本次任务授权升级的项目同步，记录来源版本与 sha256；
其他项目保持各自固定版本。项目专用工具直接在项目内维护，不强制迁到共享目录。

## 写作技能怎么调用

| 调用方 | 路径 |
|---|---|
| 规范路径 | `/home/viking/dev/docs/_shared/skills/research-writing-pipeline/SKILL.md` |
| Claude Code | `~/.claude/skills/research-writing-pipeline/SKILL.md`（兼容链接） |
| Codex | `~/.codex/skills/research-writing-pipeline/SKILL.md`（兼容链接） |

共用规则（判断 → 信息 → 措辞）在 `SKILL.md`，引用、图表、公式、证据与交付在
[`document-quality.md`](document-quality.md)。文种写法只有三类：
[`document-genres.md`](skills/research-writing-pipeline/references/document-genres.md)
按读者任务区分调研综述、工程技术文档与研究论文，给出各自的主要问题、可选骨架与连接/证据重点；
混合内容按当前段落职责处理。用户指定了会议、期刊、学校或内部规范时，按当年官方说明核对后叠加；
没有指定就按内部惯例，不硬猜目标要求。

文种由读者任务决定，标题里的「技术文档」「报告」「论文」不足以定文种；用户明确指定时以用户为准。
本目录只给入口，不复制方法正文。

配套的真实前后对照在 `../writing-examples/2026-09-20-reader-flow.md`。
校验技能结构：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    /home/viking/dev/docs/_shared/skills/research-writing-pipeline
```

本目录不新增 humanizer、质量评分器一类组件；写作流程与判断标准以
`skills/research-writing-pipeline/` 为准，交付前的检查口径以
[`document-quality.md`](document-quality.md) 为准。

## 日常只需怎么说

一句自然语言即可，不必写长 prompt：

```text
按 docs 规范把 radar-data-gen 和 ai4ai 全面检查并修复，引用统一上标，完成后给 PDF 和未决清单。
```

「全面检查并修复」默认覆盖 [`document-quality.md`](document-quality.md) 的全部检查面
（引用与参考文献、图、表、公式、证据、读者与页面、交付残留）；只审阅时明确说「不要改文件」。
执行口径、可改范围与报告要求见 [`agent-tasks/update-docs.md`](agent-tasks/update-docs.md)。
新建工程或接入外部长文时，说清项目路径、读者与交付引擎即可，其余按规范缺省。
说了读者与目的（例如「这是给工程师看的选型调研」）就按它选主文种，覆盖 agent 的推断；
不说则按项目 README、源稿与上下文推断，推断结果写进报告，不要求填表或额外确认。
若需要学习组织方式而不是只改文字，按文种读取范文库相关条目（入口 [`writing-exemplars/README.md`](writing-exemplars/README.md)），一次只读当前任务相关的一两条。

## 接收一份外部长文

最适合交给 agent 的源稿是 UTF-8 Markdown，另附独立的图片/表格文件和保留原 key 的
`references.bib` 或 DOI/URL 清单。公式使用 `$...$` / `$$...$$` 或可识别的 LaTeX 数学语法，
章节用清楚的 `#` 层级。DOCX 可以先转 Markdown；PDF 适合留作版式基线，只有 PDF 时先提取文本并人工抽查。

推荐流程：

1. 在 `/home/viking/dev/docs/<project>/source/` 保存 `original.md` 和 `assets/`，不要覆盖原稿。
2. 让 agent 读取 `/home/viking/dev/docs/AGENTS.md`、本目录写作技能和原稿上下文，选择模板并建立独立工程。
3. 让它先报告读者、章节关系、无对象反驳、推理跳步和缺失证据，再直接做有依据的局部改稿；
   只有你明确说「只审阅」时才不写文件。
4. 用 `make build` 检查构建；有旧 PDF 才用真实基线做 PDF 对比。编译通过不等于文字逻辑正确。

派工时说清项目路径、读者和交付引擎就够：

```text
在 /home/viking/dev/docs/<project> 接入 source/original.md，读者是<谁>，交付 Typst；
按 docs 规范检查并修复，保留数值、公式、引用、术语和论断强度。
```

不要求用户自己会写 Typst 或 LaTeX；用户主要提供源稿、读者和交付要求，agent 负责工程化组织，
Codex 负责范围决策与最终验收。

## 迁移记录

`paper-templates/` 与 `skills/research-writing-pipeline/` 于 2026-09-21 从
`/home/viking/dev/projects/work/paper-templates` 与
`~/.claude/skills/research-writing-pipeline` 整体移入本目录（同一文件系统，rename）。
搬移前后各出一份清单（类型/权限/属主/大小/mtime + 逐文件 sha256），逐行相同：
794 + 3 个条目、674 + 2 个文件，合并指纹
`090a9c1335a2de97e247a35f5677ababebbfe17217cdaba22e835e2c3e450633`。
