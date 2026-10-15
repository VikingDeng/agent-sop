# paper-templates — 论文与技术报告模板库

一套**正文与排版分离**的 Typst + LaTeX 写作环境。同一份正文可以复用到不同入口，
但换版式、换引擎都要**重新检查**：断行、分页、图题位置、字体嵌入、引用语法都会变，
不存在自动等价；正式投稿按目标**当年**的官方要求组装。

## 日常写作：三个默认入口

三条命令，都是分层工程（`main.typ` 只组装 + `vendor/template/` 快照 +
`template.lock`），装好 **Python 3 + Typst + GNU make** 就能离线构建：

| 写什么 | 命令 |
|---|---|
| 调研综述 | `./scripts/new_typst_paper.sh -t chinese-research -n my-survey` |
| 工程技术文档 | `./scripts/new_typst_paper.sh -t modern-technical -n my-doc` |
| 未定投稿目标的论文草稿 | `./scripts/new_typst_paper.sh -t generic -n my-paper` |

文种写在工程 `meta.typ` 的 `doc-kind` 里，命令行不猜文种。`academic-clean` /
`chinese-thesis-report` 保留为**可选版式**；`typst/` 下的会议风格模板当作**写作期的
样式预览**，不是投稿路径（选定目标后再按目标要求组装）。

---

## 一分钟上手

```bash
cd paper-templates

# 看有哪些模板可用
./scripts/list_templates.sh

# 新建一份调研综述（分层工程：main 组装 + meta + content + vendor 快照 + lock）
./scripts/new_typst_paper.sh -t chinese-research -n 2026-q3-survey
cd 2026-q3-survey && make build            # -> build/main.pdf

# 新建一份工程技术文档；论文草稿把 -t 换成 generic
./scripts/new_typst_paper.sh -t modern-technical -n design-note
```

需要会议样式预览时再用会议入口（同样只换 `-t`，但那是另一套工程形状）：

```bash
./scripts/new_typst_paper.sh -t neurips -n my-paper
cd my-paper && typst compile main.typ      # -> main.pdf
```

Windows PowerShell 用同名脚本：

```powershell
.\scripts\list_templates.ps1
.\scripts\new_typst_paper.ps1 -Template chinese-research -Name 2026-q3-survey
cd 2026-q3-survey; make build
```

---

## 会议样式预览（不是投稿路径）

同一条命令，只换 `-t`：

| 想看哪种版式 | 命令 | 用的是 |
|---|---|---|
| NeurIPS | `./scripts/new_typst_paper.sh -t neurips -n x` | `bloated-neurips` |
| ICML | `-t icml` | `lucky-icml`（本库已修过） |
| ICLR | `-t iclr` | `clear-iclr`（本库已修过） |
| CVPR | `-t cvpr` | `blind-cvpr` |
| ACL / EMNLP / NAACL | `-t acl` | `tracl` |
| IEEE 风格 | `-t ieee` | `charged-ieee` |
| JMLR / TMLR | `-t jmlr` / `-t tmlr` | `classic-jmlr` / `smooth-tmlr` |

> **重要：这些 Typst 模板全部是社区复刻，不是会议官方模板。**
> 它们适合写作期看版式；**选定投稿目标后按目标当年的官方要求组装**（多数会议
> 要求自己的 LaTeX kit，见 `latex/<会议>/` 与 `TEMPLATE_CATALOG.md`；也存在接受
> 自定义排版或 Typst 的场合，逐案核实，不要一概而论）。

不想用脚本也行 —— 直接复制现成例子：

```bash
cp -r examples/radar-paper my-paper
cd my-paper && typst compile main-neurips.typ
```

---

## 三个日常入口：职责、编辑位置与写法

```bash
./scripts/new_typst_paper.sh -t chinese-research  -n 2026-q3-survey   # 调研综述
./scripts/new_typst_paper.sh -t modern-technical  -n design-note      # 工程技术文档
./scripts/new_typst_paper.sh -t generic           -n draft-paper      # 论文草稿（目标未定）
```

| 入口 | 职责 | 正文骨架（可删改） |
|---|---|---|
| `chinese-research` | 调研综述：给需要选型或判断现状的读者 | 问题与范围 / 代表工作与机制 / 横向比较与证据 / 结论与开放问题 |
| `modern-technical` | 工程技术文档：方案、设计、验收 | 问题与约束 / 原理与方案 / 实现与接口 / 验证与限制 |
| `generic` | 投稿目标未定的论文草稿 | 引言 / 相关工作 / 方法或论证 / 结果与分析 / 结论 |

编辑位置：文种与元信息在 `meta.typ`，正文在 `content/*.typ`，文献在 `references.bib`，
图源在 `assets/`（`generic` 的摘要正文在 `content/abstract.typ`，由 `meta.typ` 载入）。
增删章节改 `main.typ` 的 `#include`，版式一律不要改 `vendor/`。

三个 starter 已经把库里的质量约定接线，正文按这些写法写就能渲染正确：

* **文献**：正文用语义 cite（`@key`），模板渲染成**上标方括号编号** `[1]`；
  文末条目的 `[1]` 保持**普通基线**。样式是 Typst 内置 `ieee`（顺序编号）。
  只有普通形式会上标；行文中的叙述式引用 `#cite(<key>, form: "prose")`（以及
  `full`/`author`/`year`）保持原样，不会整段上标。不要手写 `[1]`、不要用上标字符、
  不要正则替换数字；图表交叉引用不受影响。
* **图、表**：`#figure(kind: image, …) <fig:…>`、`#figure(kind: table, …) <tbl:…>`，
  图题在图片下方、表题在表格上方，正文要有目的地引用。
* **文献与图源来源**：每个 0.2.0 starter 自带 `references.bib`，里面只有**一条真实文献**
  （Typst 官方文档条目），用途是演示“正文上标 + 文末基线”的排版效果，**不是研究依据**；
  自带 `assets/*.svg` 是纯几何的抽象流程示意，图注里已注明“不是研究结果”。
  脚手架会把 starter 的 `references.bib` 与 `assets/` 一起复制进工程；
  旧 starter 没有这两样时沿用原来的共享文献库，也不建 `assets/`。
* **输出与清理**：产物只进 `build/`；`make build OUT='output custom/main.pdf'` 可显式改
  位置（父目录自建、支持空格路径），`make clean` 只删当前产物，`build/` 下其它文件保留。
* **模板快照边界**：`vendor/template/` 是只读快照，逐文件 sha256 记在 `template.lock`；
  `make build`/`make watch` 先跑 `make verify`（别名 `make lockcheck`），
  升级模板要显式走 README 第七节，构建**不会**自动改写 lock，也不会去模板库拉新版。

报告版式仍可用的两个可选入口：

```bash
./scripts/new_typst_paper.sh -t academic-clean        -n 综述初稿      # 纯黑白灰，适合打印
./scripts/new_typst_paper.sh -t chinese-thesis-report -n 学位论文式报告  # 封面/摘要/目录/符号表/分章
```

分层工程与会议论文工程**形状不同**：分层工程自带模板源码快照
（`vendor/template/`）+ `template.lock`，所以在装有 **Python 3 + Typst + GNU make**
的机器上就能编，不需要 `@local` / `@preview` 包，也不联网（脚本不会自动安装依赖，
缺依赖就显式失败）。详见下一节。

---

## 分层工程：模板快照 + template.lock

三个日常入口加两个可选版式，生成的工程长这样：

```
2026-q3-survey/
├── main.typ         ← 只组装：import meta.typ + include content/；没有正文、没有排版
├── meta.typ         ← 元信息唯一事实来源（标题/作者/日期/关键词/摘要）
├── content/         ← 正文，一节一文件（生成时是明确标注的占位示例）
├── assets/          ← 仅当 starter 带图源时存在（content/ 用相对路径引入）
├── vendor/template/ ← 模板源码的不可变快照：<模板>.typ + typst.toml + SOURCE.md（模板库有 LICENSE 时一并快照）
├── tools/verify_template_lock.py   ← 标准库 Python 校验器（不装第三方包）
├── template.lock    ← 模板 id / 版本 / 来源 + 快照每个文件的 sha256
├── Makefile  .gitignore  references.bib  README.md
└── build/main.pdf   ← 产物
```

工程内常用命令：

```bash
make build     # 先校验 template.lock 再编译（phony），产物 build/main.pdf
make watch     # 存盘即编译
make verify    # 校验 vendor/ 每个文件的 sha256 是否和 template.lock 一致（只读）
make lockcheck # verify 的别名，两个名字等价
make lock      # 升级模板后手动重写 lock；build/watch 永不自动改写它
make clean     # 只删当前已知产物，保留 build/ 下其它文件（如 user-note.txt）
```

产物默认 `build/main.pdf`；`make build OUT='output custom/main.pdf'` 可显式换位置
（父目录自建、空格路径可用），改到别处的产物不要提交。

标准 `make build` 需要三件都在：**Python 3**（`build` / `watch` 先跑 `make verify`
校验 `template.lock`）、**Typst**、**GNU make**。校验器只用 Python 3 标准库，
不装第三方包；脚手架和 Makefile 都**不会**自动安装依赖，缺了就显式失败
（Makefile 默认探测 `python3` 再退到 `python`，也可 `make PYTHON=/path/to/python3`）。
Windows 没有 GNU make 时用等价命令：

```powershell
python3 tools/verify_template_lock.py   # = make verify（只有 python 没 python3 时改用 python）
New-Item -ItemType Directory -Force build | Out-Null
typst compile main.typ build/main.pdf   # = make build
```

**为什么固定源码 + 记 hash。** 模板库自己的 `install-local-typst-packages.sh`
是**开发安装器**：它按 `<namespace>/<name>/<version>` 覆盖本机缓存，同一个版本号
随时可能被重新覆盖，因此它给不出「这次交付用的到底是哪一版模板」的保证。
分层工程改为把模板源码复制进 `vendor/template/`，并逐文件记 sha256：
`make build` 前先 `make verify`，谁在什么时候改了模板源码一眼可查。
本次**不改**该安装器，新的分层工程一律走 vendor 这条路。

**显式升级模板**（旧 PDF 必须提前手工保存，不能拿当前入口重编一个来冒充基线）：

```bash
cp build/main.pdf /tmp/before-template-upgrade.pdf           # 1. 存旧稿
cp <模板库>/<模板路径>/<模板>.typ vendor/template/            # 2. 覆盖快照
cp <模板库>/<模板路径>/typst.toml  vendor/template/
make lock                                                    # 3. 手动重写 lock
make build                                                   # 4. 重编
pdftotext -layout /tmp/before-template-upgrade.pdf /tmp/a.txt
pdftotext -layout build/main.pdf /tmp/b.txt && diff /tmp/a.txt /tmp/b.txt
```

「能编译」不等于「版式没变」：换模板、换引擎、换字体都要拿旧稿对照页数与逐页
文本（必要时逐页像素）。模板库里的改动**不会**自动同步到已有工程，要按上面流程
显式升级；`make build` 只校验快照没被手改，不会去模板库拉新版。

模板库侧新增一个走分层路径的模板，必须提供 `<模板目录>/starter/`（`main.typ` +
`meta.typ` + `content/`）并登记进 `templates.tsv`：**登记的是 manifest 里的行**——
`reports/*` 与 `generic-typst` 一律按分层处理，starter 只是随后被**预检**的必备文件。
登记成 `reports/<id>` 却缺 starter 时，脚本在创建任何目录之前失败，**不会**退回去找
`examples/radar-paper/` 的旧入口（那会生成依赖 `@local` 缓存、形状不同的工程）。
其他模板走会议入口，需要 `examples/radar-paper/main-<名称>.typ`；两者都没有就直接失败
退出（同样在**创建任何目录之前**），**不会**拿别的模板顶替。
构建/校验/README 等静态资源只有一份，放在 `shared/report-project/`。

---

## 我想实时预览（VS Code）

1. 用 VS Code 打开 **`paper-templates` 这个目录**（不是单个文件）。
2. 打开任意 `.typ` 文件。
3. 命令面板 `Ctrl+Shift+P` → `Tinymist: Show Preview`（或按 `Ctrl+K V`）。
   预览面板会跟着光标滚动。

保存即重绘（`tinymist.preview.refresh = onType`）。本库**故意关掉了"保存时导出 PDF"**
（`tinymist.exportPdf = never`），免得编辑过程在模板目录里堆一堆 PDF；
要出自己的 PDF，用 `typst compile` 或跑 `scripts/build_all_examples.sh`。

`.vscode/settings.json` 已按当前 Tinymist 的**真实配置项**写好（我核对过该扩展
自己的 schema，没有写记忆里的旧键名）。它只新增 Typst/LaTeX 相关键，
不动你原有的全局配置。

---

## 我想换模板

正文全在 `content/`，**入口文件是那个跟版式相关的文件**。换模板 = 换入口：

```bash
cd my-paper
cp ../examples/radar-paper/main-icml.typ main.typ   # 换成 ICML 样式预览
typst compile main.typ
```

正文可以复用，但渲染结果**不能假定等价**：换入口后要重新检查分页、断行、
图题位置与引用语法（`tracl` 连 `@key` 都要换写法）。Typst 与 LaTeX 之间
更是要人工改写正文。`examples/radar-paper/` 的意义是**一份正文配 8 个入口**，
方便对比不同版式：

```
examples/radar-paper/
├── content/            ← 正文在这里，只此一份
│   ├── _meta.typ       标题 / 作者 / 单位 / 关键词（唯一事实来源）
│   ├── _adapt.typ      把中性作者结构翻译成各会议要的形状
│   ├── abstract.typ  introduction.typ  related-work.typ
│   └── method.typ    experiments.typ   conclusion.typ
├── main-neurips.typ    ┐
├── main-icml.typ       │
├── main-iclr.typ       │  8 个入口，同一个正文
├── main-cvpr.typ       │
├── main-acl.typ        │
├── main-ieee.typ       │
├── main-generic.typ    │
└── main-report.typ     ┘  同一份正文还能直接变成技术报告
```

### 三条铁律（否则正文就不可移植了）

1. **`content/` 里只用 Typst 核心语法**：`=`、`#figure`、`#table`、数学、`@cite`。
   不要在正文里 import 任何会议包。
2. **标签一律带类型前缀**（`fig:`、`tbl:`、`sec:`、`eq:`），**参考文献 key 永远不带冒号**。
   ACL 适配器靠这条约定区分"交叉引用"和"文献引用"。
3. **作者/单位的结构调整写在 `_adapt.typ`**，不要写进正文。

### 各会议 API 不一样，这是正常的

库不追求"所有模板 API 统一"，而是把差异**全部关在入口文件和 `_adapt.typ` 里**。
实测遇到过的差异：

| 差异 | 表现 | 本库怎么处理 |
|---|---|---|
| 作者块结构 | daskol 系要 `(authors, affils)` 二元组；`charged-ieee` 要扁平单组织列表；`tracl` 要 `make-authors()` | `_adapt.typ` 里三个适配函数 |
| 引用语法 | `tracl`/pergamon 用 `#cite("key")`，不用 `@key` | `main-acl.typ` 里加 `show ref` 垫片 |
| 公式编号 | ACL 风格默认不给公式编号，`@eq:` 会报错 | `main-acl.typ` 里 `set math.equation(numbering: "(1)")` |

---

## 我想加一个新模板

1. **先确认真实存在**。查 <https://typst.app/universe/> 或上游 GitHub，
   不要凭印象写包名。核实版本、更新时间、license。
2. **下载**：`typst init @preview/<包名> typst/<会议>/`
   （`typst init` **不会**复制 license，要自己去上游仓库取一份放进去）。
3. **登记**到 `templates.tsv`（脚本靠它工作）和 `TEMPLATE_CATALOG.md`（人看的）。
4. **试编译**：`./scripts/build_all_examples.sh`。编不过就修；修不了就标 `BROKEN`，
   **不要假装成功**。
5. **如果修了上游**（像本库对 ICML/ICLR 做的那样），写一份 `PATCHES.md` 说明改了哪一行、
   为什么、上游是否已修，并把改过的模板装成本地包：
   `./scripts/install-local-typst-packages.sh`
6. 写一个 `main-<会议>.typ` 入口放进 `examples/radar-paper/`（正文骨架复用，
   换入口后按第 4 步重新编译检查）。
7. 如果要做成**分层工程模板**（`reports/<id>/`，或像 `typst/generic/` 那样自带
   starter）：必须给出 `starter/main.typ`、`starter/meta.typ`、`starter/content/`
   （正文用明确标注的占位示例，不要把真实报告抄进骨架）；starter 可自带
   `references.bib` 与 `assets/`（脚手架会一起复制）；共用静态资源留在
   `shared/report-project/`，不要在每个模板下各抄一份 Makefile / 校验器。
   脚手架按 **manifest 判断**走哪条路径：`templates.tsv` 里路径为 `reports/*` 的行和
   `generic-typst` 一律按分层模板处理——挑 starter 之前先预检 `starter/{main.typ,meta.typ,
   content/}`，缺一个就在建目录前失败，**不会**退回 `examples/radar-paper/` 的会议入口；
   其他行才走会议入口，入口也缺就直接失败。
   模板版本号要同时改 `typst.toml` 与 `templates.tsv`，并用 `example.typ` 与旧稿对照。

新增的模板必须保留原作者的 license 与署名。社区复刻**不许**标成官方模板。

---

## 目录结构

```
paper-templates/
├── README.md                ← 你在看的这份
├── TEMPLATE_CATALOG.md      模板总表：来源 / 年份 / 官方还是社区 / 能否投稿 / 评分
├── ENVIRONMENT.md           本机环境实测记录
├── BUILD_REPORT.md          编译验证报告（22 个目标，逐个结果 + 日志）
├── templates.tsv            机器可读的模板清单（脚本的数据源）
│
├── typst/                   会议/通用排版模板
│   ├── neurips/ icml/ iclr/ cvpr/ acl/   ← 会议样式预览（社区复刻）
│   ├── generic/             未定投稿目标的论文草稿（generic-paper + starter/ + LICENSE）
│   ├── ieee/                 charged-ieee · bamdone-ieeeconf · ieee-vgtc
│   ├── radar/                ISPRS（遥感）
│   └── iccv/ eccv/ emnlp/ aaai/ ijcai/ kdd/ sigir/ www/   ← 暂无可靠 Typst 模板，内有说明
│
├── latex/                   官方 LaTeX author kit（正式投稿用）
│   ├── PROVENANCE.md        每个 kit 的下载来源、commit/ETag、sha256、被拒的来源
│   ├── eccv/2026/           当前 ECCV 入口（SOURCE.md + SHA256SUMS）；eccv/kit/ 是 2022 历史
│   └── <会议>/PROVENANCE.txt
│
├── reports/                 自建分层文档模板（三个日常入口之二 + 两个可选版式）
│   ├── chinese-research/    调研综述（默认入口）
│   ├── modern-technical/    工程技术文档（默认入口）
│   ├── academic-clean/      黑白灰，打印友好（可选版式）
│   ├── chinese-thesis-report/  中文论文式长报告（封面/摘要/目录/符号表/分章，可选版式）
│   └── <每个模板>/          starter/（脚手架骨架）+ example.typ（库内演示）
│                            chinese-plain/ 未登记、未接入脚手架（见「已知限制」）
│
├── examples/radar-paper/    内容与模板分离的示范工程（8 入口 + 1 份正文）
│
├── shared/                  可复用素材
│   ├── report-project/      报告工程共用静态资源（Makefile / .gitignore / README / lock 校验器）
│   ├── bibliography/        起步用 .bib
│   ├── content/             会议论文工程的正文骨架
│   ├── figures/  styles/
│
├── vendor/                  个别模板的自建快照（elegant-mono 未接入脚手架）
│
└── scripts/                 辅助脚本（.sh 与 .ps1 成对）
```

---

## 脚本

| 脚本 | 干什么 |
|---|---|
| `check_environment.sh` / `.ps1` | 检查 typst / xelatex / lualatex / latexmk / git / code / 字体 / 扩展 |
| `list_templates.sh` / `.ps1` | 列出模板：ID、会议、版本、年份、官方还是社区、路径、状态 |
| `new_typst_paper.sh` / `.ps1` | 建新工程：`-t` 选模板、`-n` 工程名、`-d` 父目录。分层工程（`templates.tsv` 里 `reports/*` + `generic-typst`，三个日常入口 + 两个可选版式）= main/meta/content/vendor 快照/lock/Makefile，starter 带 `assets/`、`references.bib` 时一并复制；会议入口=正文骨架+对应入口+bib+图占位。未知模板、不可用状态、缺 starter/入口都会在创建目录前失败（登记为分层的模板缺 starter 时不会退回会议入口），目标非空默认拒绝（`--force` 除外） |
| `build_all_examples.sh` / `.ps1` | 编译所有示例与模板，写 `BUILD_REPORT.md`；`--reports-only` 只编报告（目标从 `templates.tsv` 读），`--no-report` 不写报告。成功=编译返回 0 **且** PDF 存在 |
| `build_latex_kits.sh` | 编译 `latex/` 下全部官方 author kit（在临时副本里编，不弄脏模板） |
| `install-local-typst-packages.sh` | 把改过的模板装成 Typst 本地包（改完 `typst/icml` 之类要重跑） |

`.ps1` 与 `.sh` 功能一致。**两套都在本机实测过** —— 为此装了 PowerShell 7.6.6
（见 `ENVIRONMENT.md`）。`build_latex_kits.sh` 只有 bash 版。

### 编译验证结果

`BUILD_REPORT.md` 由脚本生成，不是手写的：

* **Typst：22 个目标，22 成功，0 失败**（8 个共用同一份正文的入口 + 3 个报告模板 + 11 个库内模板）
* **LaTeX：11 个官方 author kit，11 成功，0 失败**（neurips / icml / iclr / cvpr / iccv / eccv / acl / aaai / ijcai / ieee / kdd）
* 上面这条是 **2026-09-17** 的记录，当时 `eccv` 编的是 **2022** kit；ECCV 入口现已是 2026 kit。
  **ECCV 2026 kit 单独重编（2026-09-23）**：`latex/eccv/2026/kit/main.tex`，15 页，逐页文本与
  官方参考 PDF 相同（`BUILD_REPORT.md` 未改写）。来源、commit 与 sha256：
  [`latex/eccv/2026/SOURCE.md`](latex/eccv/2026/SOURCE.md)、`latex/eccv/2026/SHA256SUMS`。

生成的 PDF 在 `build/`，可以直接拿去看效果。

```bash
./scripts/build_all_examples.sh      # Typst，重写 BUILD_REPORT.md
./scripts/build_latex_kits.sh        # LaTeX，追加到 BUILD_REPORT.md
```

---

## 常用命令备忘

```bash
typst compile main.typ                 # 编一次
typst watch   main.typ                 # 存盘即编
typst compile main.typ --font-path /path/to/fonts   # 临时加字体
typst init @preview/<pkg> <dir>        # 拉一个新模板
typst --version
```

```bash
./scripts/build_all_examples.sh        # 全量编译 + 出报告
./scripts/build_all_examples.sh --quick   # 跳过模板自带 demo
make build OUT='output custom/main.pdf'   # 分层工程：产物换位置（父目录自建、空格路径可用）
```

LaTeX 侧（正式投稿）：

```bash
cd latex/<会议>/
latexmk -pdf main.tex          # 或 -xelatex，看该目录 PROVENANCE 说明
```

---

## 字体

模板要求商业字体时**不会**导致编译失败 —— Typst 会在字体列表里往后找可用的，
PDF 里嵌入的是真正用到的那一款。本机装了 TeX Gyre 全家族（Times/Palatino/
Helvetica 的度量兼容开源替代），并加了 `~/.config/fontconfig/fonts.conf`
把 `Times New Roman → TeX Gyre Termes`、`Arial → TeX Gyre Heros` 等做了别名。

编译时若看到 `warning: unknown font family: times new roman`，那是**良性提示**
（列表里第一个名字没装，已用后面的替代），不是错误。

**中文稿要显式写 CJK 字体家族**：本机实测，字体列表里没有 CJK 家族时，Typst 的字形
回退会挑到**日文** CJK 字体（甚至混用 Kai/IPA 等），中文字形不对但不报错。
三个 0.2.0 starter 现在只传 `lang: meta.lang`（`meta.typ` 里是 `"zh"`）：**模板按 lang
选字体栈**，中文以 `Noto Serif/Sans CJK SC` 为首选、Source Han 同名家族次选，摘要 /
关键词 / 目录标签也由 lang 给中文默认值；显式传 `font` / `heading-font` /
`toc-title` / `abstract-label` / `keywords-label` 时仍以调用方为准。
`modern-technical` 的英文默认栈把 CJK 家族加在末尾（只影响本来就没有字形覆盖的字符，
拉丁文渲染不变）。模板不会下载或安装字体。

---

## 引擎、模板与正式交付

- **同引擎换模板也要重新检查排版**：文字一样不代表断行、分页、字号、页眉一样。
  最低要求是拿旧稿逐页比文本（`pdftotext -layout`），改版式相关的改动再比页数/像素。
- **Typst 正文与 LaTeX 正文不自动互换**：`= 标题`、`#figure`、`$公式$` 这些
  Typst 语法搬到 LaTeX 必须人工改写，没有一键转换。`examples/radar-paper/`
  的「一份正文、多个入口」只在 Typst 模板之间成立。
- **正式交付按接收方当年的官方要求**：以目标会议/期刊/学校**当年**的 author
  kit、模板版本和投稿说明为准；本库 `latex/<会议>/` 是官方 kit 存档，但规则会
  逐年变化。**不要一概声称「Typst 都不允许投稿」**——有的场合接受自定义排版，
  有的明确要求官方模板，逐案核对 `TEMPLATE_CATALOG.md` 与对方最新说明。
- 会议类 Typst 模板都是社区复刻；`reports/` 下与 `typst/generic/` 的自建模板是
  内部模板。两者都不构成任何投稿或学位合规承诺。

---

## 已知限制

- `typst/iccv|eccv|emnlp|aaai|ijcai|kdd|sigir|www|radar/` 下**没有**可靠的 Typst 模板。
  这些目录里放的是情况说明，不是伪造的模板。这些会议请用 `latex/<会议>/` 的官方模板
  （EMNLP 与 ACL 共用 ACL 官方样式；KDD/SIGIR/WWW 用 ACM `acmart`）。
- **ECCV 的官方 kit 已是 2026 版**：入口 `latex/eccv/2026/kit/main.tex`（GitHub
  `paolo-favaro/paper-template` tag `Latest` @ commit `da8c09c4`）；`latex/eccv/kit/`
  （2022）只作历史保留。ECCV 2026 的投稿页同时允许用 Springer LNCS **Word** 模板，
  本库只存 LaTeX kit。来源与 sha256：[`latex/eccv/2026/SOURCE.md`](latex/eccv/2026/SOURCE.md)。
- Typst 模板都是**社区复刻**。它们模仿的是某年的会议样式，不等于该会议接受。
- `@preview/lucky-icml:0.7.0` 与 `@preview/clear-iclr:0.7.0` 在 Typst 0.15 上**编不过**。
  本库已 vendored 并修好，装成 `@local/lucky-icml:0.7.1` / `@local/clear-iclr:0.7.1`。
  细节见 `typst/icml/PATCHES.md`、`typst/iclr/PATCHES.md`。
- 修改 `typst/icml`、`typst/iclr`、`typst/generic`、`reports/*` 之后，如果还要用
  `@local` 的**库内演示入口**（如 `examples/radar-paper/main-generic.typ`），
  要重跑 `scripts/install-local-typst-packages.sh`，否则 `@local` 包还是旧的。
  注意该脚本是**开发安装器**：它按版本号覆盖本机缓存，**不提供不可变锁**。
  新生成的分层工程（含 `-t generic`）不走 `@local`，模板源码在工程的
  `vendor/template/` 里并用 `template.lock` 记录 sha256（见「分层工程」一节）。
  `typst/generic/typst.toml` 升到 0.2.0 后，本机缓存的 `@local/generic-paper:0.1.0`
  仍是 0.1.0 快照，老演示入口的行为不变。
- `reports/chinese-plain` 与 `vendor/elegant-mono` **未接入脚手架**：不在
  `templates.tsv` 里、没有 `starter/`，`new_typst_paper` 会明确拒绝而不是拿
  别的模板顶替。本轮只如实记录，不做扩展。
