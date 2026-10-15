# ECCV — LaTeX author kit

**投稿 ECCV 2026 用 [`2026/kit/main.tex`](2026/kit/main.tex)。** 这是官方作者套件原样收录，
入口与上游一致；本库没有把它包装成我们的正文工程，也没有通用 LaTeX 生成器。

- `2026/` — ECCV 2026 Author Kit，取自官方页面指向的 GitHub `paolo-favaro/paper-template`
  仓库 `Latest` 标签（commit `da8c09c40239d5665757527e77388f4716a6564a`）。
  来源链、许可与核验范围见 [`2026/SOURCE.md`](2026/SOURCE.md)，逐文件哈希见
  [`2026/SHA256SUMS`](2026/SHA256SUMS)，原始归档 `2026/_original.tar.gz`。
- `kit/` — **ECCV 2022** 套件（入口 `eccv2022submission.tex`），仅历史留档。官方页面写明
  模板自 ECCV 2024 起已变更，所以它不能用于 2026 投稿。
- `PROVENANCE.txt` — 2022 那轮抓取的记录，保持原样未改。

编译按包内 `README.md`：`pdflatex main` → `bibtex main` → `pdflatex main` ×2（等价地用
`latexmk`）。`scripts/build_latex_kits.sh` 只在临时副本里编译，不会往这里写中间文件。

正式投稿以**目标年份**的官方要求为准：换年份就换当年官方 kit，不用旧 kit 顶替。
