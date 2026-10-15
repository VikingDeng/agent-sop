# __PROJECT_NAME__ — __TEMPLATE_ID__ 分层文档工程

用模板库 `paper-templates` 的 **__TEMPLATE_ID__ __TEMPLATE_VERSION__** 模板生成。
排版固定在 `vendor/template/`，正文在 `content/`，入口 `main.typ` 只负责组装。

模板库的三个日常入口都走这套分层工程：**调研综述**（`chinese-research`）、
**工程技术文档**（`modern-technical`）、**尚未确定投稿目标的论文草稿**
（`generic`）；`academic-clean` / `chinese-thesis-report` 仍是可选报告版式。
文种由本工程的 `meta.typ` 决定，不由脚手架猜。

---

## 一、常用命令

```bash
make build     # 先校验 template.lock 再编译到 build/main.pdf（phony：每次都重编，不拿旧 PDF 糊弄）
make watch     # 存盘即编译（同样先校验 lock）
make verify    # 校验 vendor/ 快照的 sha256 是否和 template.lock 一致
make lockcheck # verify 的别名，两个名字等价
make lock      # 升级模板后显式重写 template.lock（build 不会自动改它）
make clean     # 只删已知构建产物，保留 build/ 下其它文件
make version   # 打印本机 typst 版本
```

* 产物默认只进 `build/`。要换位置是显式动作：

  ```bash
  make build OUT='output custom/main.pdf'   # 父目录自动创建，路径可带空格
  ```

  改到别处的产物**不要提交**；`make clean` 只删当前 `$(OUT)` 这一个已知产物。
* **标准 `make build` 需要三样都在本机**：**Python 3**（`build` / `watch` 会先跑
  `make verify` 校验 lock）、**Typst**、**GNU make**。缺任何一样都不是可用的标准流程；
  脚手架和 Makefile 都**不会**替你安装依赖，缺了就直接失败（Python 解释器默认探测
  `python3` 再退到 `python`，也可 `make PYTHON=/path/to/python3 ...` 显式指定）。
* 引擎版本：本工程快照**实测 typst 0.15.1**（`make version`）。模板的**最低声明版本**
  看 `vendor/template/typst.toml` 的 `compiler` 字段——那是模板作者声明的下限，
  不等于「该下限以上的每个版本都验证过」；换引擎版本要按第七节重编并与旧稿对照。
* Windows 上没装 GNU make 时，用等价的 PowerShell 命令：

```powershell
python3 tools/verify_template_lock.py                # = make verify（只有 python 没 python3 时改用 python）
New-Item -ItemType Directory -Force build | Out-Null
typst compile main.typ build/main.pdf                # = make build
Remove-Item build/main.pdf                           # = make clean（只删已知产物）
```

* 校验脚本 `tools/verify_template_lock.py` **只用 Python 3 标准库**，不装第三方包。
  Python 3 是标准构建的必需项，不是可选项：没有它 `make build` 完不成 lock 校验，
  请先在本机装好 Python 3（本工程不会自动安装任何东西）。**不要**把「跳过 lock 校验、
  直接 `typst compile`」当常规流程——那等于放弃「这次编的到底是哪版模板」的追溯。
* 想临时换引擎参数：`make build FLAGS="--font-path /path/to/fonts"` 或
  `make build TYPST=/path/to/typst`。

---

## 二、目录结构

```
__PROJECT_NAME__/
├── main.typ                      ← 入口：只组装（import 元信息 + include 章节），不含正文/排版
├── meta.typ                      ← 元信息唯一事实来源（标题/作者/日期/关键词/摘要）
├── content/                      ← 正文，一节一文件
│   └── ...                          纯 Typst，不写全局排版（#set page 之类属于模板）
├── assets/                       ← 仅当模板 starter 自带图源时存在；content/ 用相对路径引入
├── vendor/template/              ← 模板源码的**不可变快照**（含 typst.toml + SOURCE.md 来源说明；
│                                   模板库里该模板带许可文件时，LICENSE 等一并快照）
├── tools/verify_template_lock.py ← lock 校验器（标准库）
├── template.lock                 ← 模板 id / 版本 / 来源 / 快照每个文件的 sha256
├── references.bib                ← 文献库（起步内容见第四节，交付前替换）
├── Makefile / .gitignore
└── build/                        ← 构建产物（git 忽略）
    └── main.pdf
```

`content/` 里的文件是**明确标注的示例/占位正文**，请逐段替换成你自己的内容。

---

## 三、改哪里

| 想改什么 | 改哪个文件 |
|---|---|
| 标题、作者、日期、关键词等一般元信息 | `meta.typ` |
| 文种标签（页眉/封面上的“调研综述”“工程技术文档”等） | `meta.typ` 的 `doc-kind`；文种不靠命令行猜 |
| 摘要 | 一般也在 `meta.typ`（字段名随模板而变，如 `summary` / `abstract`，以生成的 `main.typ` 实际传入的参数为准）；论文草稿（`generic`）的摘要正文在 `content/abstract.typ`，由 `meta.typ` 用 `include` 载入；长报告（如 `chinese-thesis-report`）的中英文摘要正文在 `content/abstract*.typ`——不要假设所有模板的摘要位置都一样 |
| 某一节正文 | `content/*.typ` |
| 增删章节、调顺序 | `main.typ`（加/删一行 `#include`），同时按需删掉对应 `content/` 文件 |
| 文献 | `references.bib`（写法见第四节） |
| 图源（仅 `assets/` 存在时） | `assets/*.svg`；正文用 `#image("../assets/…")` 引入 |
| 通用版式（页边距、字号、页眉页脚、表格样式） | **不要直接改** `vendor/`，见第七节 |

编辑规矩：

1. **一文件一职责**：`main.typ` 只组装；`meta.typ` 只有元信息；`content/` 只有正文。
2. **不要动 `vendor/`**：它是模板快照，改了就和 `template.lock` 的 sha256 对不上，
   `make build` 会先失败；升级模板请走第七节。
3. **`content/` 里要用模板提供的积木必须自己 import**，Typst 的 import 不跨文件继承；
   各模板导出的辅助名字**并不相同**，只能 import 你所用模板确实导出的：

   | 模板 | `content/` 可用的辅助积木 | 三线表 helpers |
   |---|---|---|
   | `chinese-thesis-report` | `three-line-table`、`caption-above`、`caption-below`、`rule` | 有 |
   | `modern-technical` | `callout`、`key-findings`、`rule` | 无（用核心 `#table` 自己写） |
   | `academic-clean` | `note`、`abstract-block`、`rule` | 无（同上） |
   | `chinese-research` | `zh-callout`、`zh-key-points`、`rule` | 无（同上） |
   | `generic`（论文草稿） | 无 helper：正文只用核心 Typst（`=`、`#figure`、`#table`、`$公式$`、`@key`） | 无（同上） |

   例（**只有 `chinese-thesis-report` 导出这三个 helpers**，别照抄到别的模板）：

   ```typst
   #import "../vendor/template/chinese-thesis-report.typ": three-line-table, caption-above, rule
   ```

   上表按模板库 `0.2.0` 快照逐个核对；本工程用的是 `__TEMPLATE_ID__`，模板更新后以
   `vendor/template/__TEMPLATE_ID__.typ` 里的 `#let` 为准，最贴近本工程的现成用法是
   `content/` 骨架里的 import 行。

4. **不要在正文里 `#set page` / `#set text` 做全局排版**，那些属于模板。
   文种写在 `meta.typ` 的 `lang`（三个 starter 默认 `"zh"`）：模板按 lang 选字体栈
   （中文以 `Noto Serif/Sans CJK SC` 为首选）与中文标签（摘要 / 关键词 / 目录）。
   要显式覆盖字体或标签时，在 `main.typ` 的模板参数里传 `font` / `heading-font` /
   `toc-title` / `abstract-label` / `keywords-label`，调用方的值优先。

---

## 四、引用、图、表的写法（模板已接线）

* **文献引用用语义 cite**：正文写 `@key`，由模板渲染成**上标方括号编号**（`[1]`），
  位置在受支持短语之后、句末标点之前；**文末参考文献条目的 `[1]` 保持普通基线**。
  只有普通形式会上标；行文里的叙述式引用写 `#cite(<key>, form: "prose")`
  （`full` / `author` / `year` 同理），模板保持它们原本的语义与基线。
  不要手写 `[1]`、不要用上标字符、不要正则批量替换数字。
  样式用 Typst 内置 `ieee`（顺序编号），在 `main.typ` 的
  `bibliography("/references.bib", style: "ieee")` 里指定。
  只作用于文献引用；`@fig:` / `@tbl:` / `@eq:` 这类交叉引用仍是普通行内引用。
* **图、表要有确定种类和稳定 label**：图用 `#figure(kind: image, …) <fig:…>`，
  表用 `#figure(kind: table, …) <tbl:…>`，公式用 `<eq:…>`；
  图题在图片下方、表题在表格上方（模板统一控制），正文要有目的地引用它们。
* **`references.bib` 起步内容**：`chinese-research` / `modern-technical` / `generic`
  三个 starter 各带一条**真实**文献（Typst 官方文档），只用于演示“正文上标 + 文末基线”
  的排版效果，**不是研究或技术依据**；其他旧 starter 沿用模板库的共享文献库。
  交付前请整体替换为自己的文献，不要留下示例条目。
* `assets/` 里的图是 starter 自带的**排版示例**（纯几何抽象流程），图注里已注明
  “不是研究结果”；换成自己的图源时保留可编辑源文件。

---

## 五、模板来源与版本

| 项 | 值 |
|---|---|
| 模板名 | `__TEMPLATE_ID__` |
| 版本 | `__TEMPLATE_VERSION__` |
| 来源 | 模板库 `__TEMPLATE_PATH__`（origin: `__TEMPLATE_ORIGIN__`） |
| 许可 | `__TEMPLATE_LICENSE__` |
| 快照 | `vendor/template/`，逐文件 sha256 记在 `template.lock` |
| 本工程由 | `__SCAFFOLD_SCRIPT__` 于脚手架生成 |

模板自己的文档（参数表、可用积木、字体说明）在模板库同名目录的 `README.md`；
本工程 `vendor/template/` 只有源码快照，是**只读**的。

---

## 六、引擎与字体

字体走候选列表，本机装哪个用哪个；缺字体只会打印
`warning: unknown font family: ...`（候选回退提示），不影响编译，但**不是零警告**。
想固定字体，在 `main.typ` 的模板参数里传 `font` / `heading-font` 覆盖，不要改
`vendor/`。中文稿只需要在 `meta.typ` 写 `lang: "zh"`：模板据此把
`Noto Serif/Sans CJK SC`（Source Han 同名家族次选）排在最前——本机实测，字体列表里
没有 CJK 家族时 Typst 的字形回退会落到日文 CJK 字体，中文字形不对。模板不会下载字体。

---

## 七、升级模板（显式流程）

**关键：变更前的旧 PDF 必须提前手工保存，不能拿当前入口重编一个来冒充基线。**

```bash
# 1. 升级前，先手工保存旧稿（唯一合法的对比基线）
cp build/main.pdf /tmp/before-template-upgrade.pdf

# 2. 用模板库里的新版覆盖快照（只覆盖 vendor/，不动正文）
cp <模板库>/__TEMPLATE_PATH__/__TEMPLATE_ID__.typ vendor/template/
cp <模板库>/__TEMPLATE_PATH__/typst.toml           vendor/template/
#    模板库若同时更新了许可/来源文件（如 LICENSE），也一并同步进 vendor/template/

# 3. 手动重写 lock（build 永不自动改写）
make lock

# 4. 重新编译，并用原稿 PDF 做内容/版式比较（页数、逐页文字、必要时逐页像素）
make build
pdftotext -layout /tmp/before-template-upgrade.pdf /tmp/before.txt
pdftotext -layout build/main.pdf /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt && pdfinfo build/main.pdf | grep Pages
```

模板升级后出现差异时，先判断是「本来就该改成这样」还是「改坏了」，
**不要用“编译成功”当验收**。换引擎版本同理：即使换回同一模板，也必须重新检查排版。

---

## 八、交付与引擎选择的提醒

* 本工程是**内部分层工程**形态：调研综述 / 工程技术文档 / 未定投稿的论文草稿，
  不是会议投稿入口。选了具体投稿目标之后，按目标**当年**的官方要求组装
  （模板库 `latex/<会议>/` 是官方 author kit 存档），不要预设有某个会议的默认版式。
* **Typst 与 LaTeX 的正文不能自动互换**：本文正文用的是 Typst 语法（`= 标题`、
  `#figure`、`$公式$`），迁到 LaTeX 需要人工改写，不存在一键转换。
* 不同引擎/不同模板渲染同一段文字，断行、分页、字体嵌入都会变；
  正式交付前按接收方的要求（引擎、模板版本、页数、字体）逐项核对。
