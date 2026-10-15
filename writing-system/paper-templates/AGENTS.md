# AGENTS.md — paper-templates 模板库

本目录是**模板库**，不是某一篇文档的工程目录。改这里的文件会影响之后所有新建工程。

## 先看哪里

| 要做什么 | 看/改 |
|---|---|
| 有哪些模板、状态如何 | `templates.tsv`（机器可读，脚本唯一数据源）+ `TEMPLATE_CATALOG.md`（人看） |
| 新建文档 | `scripts/new_typst_paper.sh` / `.ps1`（`.sh` 与 `.ps1` 行为必须对应） |
| 编译验证 | `scripts/build_all_examples.sh` / `.ps1`（`--reports-only` 可精准只编报告） |
| 报告工程的共用静态资源 | `shared/report-project/`（Makefile / .gitignore / README 模板 / lock 校验器） |

## 硬规则

1. **报告模板必须分层**：`reports/<id>/` 下提供 `starter/{main.typ,meta.typ,content/}`；
   生成的工程是 `main.typ`（只组装）+ `meta.typ` + `content/` + `vendor/template/`
   快照 + `template.lock` + `Makefile`，产物进 `build/`。不要在 `main.typ` 里写正文。
   模板不是冻死的：有**通用**需求时改库内模板本身（不是某个工程的 `vendor/` 副本），
   同时升版本（`typst.toml` + `templates.tsv`）、用 `example.typ` 编译并与旧稿对照，
   再让受影响的文档工程显式升级 `vendor/` 快照和 `template.lock`。
2. **不静默兜底**：未知模板、`state` 不可用、缺 `starter/`/入口文件，都必须在
   **创建任何目录之前**明确失败；绝不拿 generic 或别的模板冒充。目标目录非空默认
   拒绝，只有显式 `--force` 才写入。路径要能带空格。
3. **模板源码要可追溯**：`vendor/` 只放必要的模板源码、`typst.toml`、许可/来源文件，
   不递归复制 `starter/`；`template.lock` 记录 id/版本/来源/逐文件 sha256。
   构建前校验，**构建不自动重写 lock**；升级是显式动作。
4. **构建结果不许造假**：脚本只有「编译返回 0 **且** 产物存在」才算成功；
   旧 PDF、半截 PDF 都不能当成功。历史 `BUILD_REPORT.md` 记录的**验收事实要保留、
   不许改写**；本次这类局部检查用 `--reports-only --no-report`（不写报告）验证即可，
   但这不是永久禁止生成新报告——需要重新全量验收时照常重写。
5. **正文示例只能是占位**：骨架里的正文必须明确标注为示例/占位，不要把任何真实
   报告或研究结论抄进公共骨架；**不虚构学术数据、指标或引用**。
6. **改完必须自证**：`bash -n` 所有改动的 shell；PowerShell 脚本至少过语法解析，
   能跑就实跑；改动报告脚手架后，在 `/tmp` 生成工程并 `make build` 通过，
   含空格父目录、独立目录副本、篡改 lock 必须失败、`make clean` 保留
   `build/user-note.txt`。不给「应该可以」的结论，只给命令与输出。
7. **版本与交付**：同一模板换引擎/换版本也要重新比对旧稿 PDF（页数 + 逐页文本）；
   Typst 与 LaTeX 正文不自动互换；正式交付以接收方**当年**官方要求为准，
   不要一概声称某引擎不被接受。许可与来源必须随模板保留，社区复刻不许标成官方。

## 协作

- 架构与验收决策由 Codex 负责；重复性、耗时的执行优先交给
  `dsh --profile headless`。派工时写清：目录、验收标准、边界（不许改什么）、
  期望输出与证据路径。
- 需要动用户已有工程时，先在 `/tmp` 留备份快照，不覆盖已有快照。
