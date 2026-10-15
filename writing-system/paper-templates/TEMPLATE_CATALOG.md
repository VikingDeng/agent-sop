# TEMPLATE_CATALOG

Every template in this library, what it actually is, and whether you may submit with it.

**Verified:** 2026-09-17, against the complete Typst Universe package index (1,601
preview packages) and the upstream repositories named below. Versions, dates and
repo activity in this file were read from the sources, not recalled.
**That verification is historical.** The 2026-09-23 template update (three daily
entries, versions 0.2.0) did not re-check any venue online; the one later check is
the **ECCV 2026** row, re-verified against the official ECCV 2026 submission page
on 2026-09-23 (`latex/eccv/2026/SOURCE.md`). No other venue statement below was
re-verified in that round. Submission rules change yearly: check the target's
*current-year* author instructions yourself before relying on any row here.

## Start here: the three daily entries

| What you are writing | Command | Template |
|---|---|---|
| 调研综述（survey / review） | `./scripts/new_typst_paper.sh -t chinese-research -n my-survey` | `chinese-research` 0.2.0 |
| 工程技术文档（design / technical document） | `./scripts/new_typst_paper.sh -t modern-technical -n my-doc` | `modern-technical` 0.2.0 |
| 论文草稿，投稿目标未定 | `./scripts/new_typst_paper.sh -t generic -n my-paper` | `generic-paper` 0.2.0 |

All three produce the same layered project (assembly-only `main.typ` + `meta.typ`
+ `content/` + a frozen `vendor/template/` snapshot + `template.lock` + `Makefile`),
so they build offline with Python 3 + Typst + GNU make. `academic-clean` and
`chinese-thesis-report` remain available as **optional report layouts**; the
three entries above are the ones that carry a document kind ("调研综述",
"工程技术文档", "paper draft"). A venue is chosen *after* the draft exists —
only then does it make sense to assemble the submission from that venue's own
official kit. No venue is pre-selected, and nothing is converted automatically
between templates or engines.

**The one rule this document exists to enforce:** everything under `typst/` is a
**community reimplementation** of a venue's *look*. None of them is published,
endorsed or accepted by the venue. `latex/` holds the real submission artifacts.

---

## Master table

| Venue | Typst | LaTeX | Source of the LaTeX kit | Official? | Year | Verified | Submission note |
|---|---|---|---|---|---|---|---|
| NeurIPS | ✅ `bloated-neurips` | ✅ | `media.neurips.cc` Styles.zip | **yes** (LaTeX) | 2025 / 2026 style | 2026-09-17 | LaTeX only. NeurIPS does not accept Typst. |
| ICML | ✅ `lucky-icml` *(patched)* | ✅ | `media.icml.cc` icml2026.zip | **yes** (LaTeX) | 2026 | 2026-09-17 | LaTeX only. |
| ICLR | ✅ `clear-iclr` *(patched)* | ✅ | `github.com/ICLR/Master-Template` @`46ed6f4c` | **yes** (LaTeX) | iclr2027 | 2026-09-17 | LaTeX only. |
| CVPR | ✅ `blind-cvpr` | ✅ | `github.com/cvpr-org/author-kit` @`29175854` | **yes** (LaTeX) | CVPR 2026 | 2026-09-17 | LaTeX only. |
| ICCV | ❌ none | ✅ | `media.eventhosts.cc` ICCV2025 Author Kit | **yes** (LaTeX) | 2025 | 2026-09-17 | LaTeX only. ICCV has its **own** kit, not just the CVPR one. |
| ECCV | ❌ none | ✅ *(2026 kit)* | ECCV 2026 kit: GitHub `paolo-favaro/paper-template` @`da8c09c4` (tag `Latest`) | **yes** (LaTeX) | **2026** | 2026-09-23 | Official **LaTeX** kit at `latex/eccv/2026/kit/`; the 2022 kit stays as history. ECCV uses **`llncs.cls`**, not `cvpr.sty`. The same submission page also allows a **Word** paper built on the official Springer LNCS Word template — this library stores the **LaTeX** kit only. Source: `latex/eccv/2026/SOURCE.md`. |
| ACL | ✅ `tracl` | ✅ | `github.com/acl-org/acl-style-files` @`d5adc823` | **yes** (LaTeX) | current | 2026-09-17 | LaTeX only. |
| EMNLP | ⚙️ reuse `tracl` | ✅ | byte-identical to ACL | **yes** (LaTeX) | current | 2026-09-17 | EMNLP ships no separate kit; it uses the *ACL style files. |
| AAAI | ❌ none | ✅ | `aaai.org/authorkit27` | **yes** (LaTeX) | 2027 | 2026-09-17 | LaTeX only. |
| IJCAI | ❌ none | ✅ | `ijcai.org` IJCAI-ECAI-26 kit | **yes** (LaTeX) | 2026 | 2026-09-17 | LaTeX only. |
| KDD | ❌ none | ✅ | ACM `acmart-primary.zip` v2.20 | **yes** (publisher) | 2026 | 2026-09-17 | ACM `acmart` in `sigconf`. |
| SIGIR | ❌ none | ✅ | ACM `acmart-primary.zip` v2.20 | **yes** (publisher) | 2026 | 2026-09-17 | ACM `acmart` in `sigconf`. |
| TheWebConf (WWW) | ❌ none | ✅ | ACM `acmart-primary.zip` v2.20 | **yes** (publisher) | 2026 | 2026-09-17 | ACM `acmart` in `sigconf`. |
| IEEE (general) | ⚙️ `charged-ieee` *(drafting only)* | ✅ | CTAN `IEEEtran` v1.8b | **yes** (LaTeX) | 1.8b | 2026-09-17 | IEEE does not accept Typst. |
| IEEE Radar / IGARSS | ❌ none | ✅ | IEEEtran conference mode | **yes** (LaTeX) | 1.8b | 2026-09-17 | RADAR 2026's own author page mandates IEEEtran conference mode. |
| IEEE TGRS / GRSL / TAES / T-RS | ❌ none | ✅ | IEEEtran journal mode | **yes** (LaTeX) | 1.8b | 2026-09-17 | Use the journal option of IEEEtran. |
| ISPRS | ✅ `magic-isprs` | — | — | community | current | 2026-09-17 | Community Typst template for an ISPRS venue. Not checked against ISPRS rules. |
| JMLR | ✅ `classic-jmlr` | — | — | community | current | 2026-09-17 | Drafting. JMLR's own style is LaTeX. |
| TMLR | ✅ `smooth-tmlr` | — | — | community | current | 2026-09-17 | Drafting; TMLR accepts a wide format but check the current policy. |
| — (generic) | ✅ `generic-paper` | — | — | **this library** | — | 2026-09-17 | Layered draft project; no venue, no submission claim. Daily entry for an undecided target. |
| — (reports ×4 + generic) | ✅ | — | — | **this library** | — | 2026-09-17 | Internal documents, not submissions. Five templates now scaffold layered projects (3 daily entries + 2 optional layouts). |

Legend: ✅ present · ⚙️ reuse another template · ❌ none exists · ⚠️ partial/stale.

> `latex/` covers all 15 venues. Its download record — exact URL, HTTP ETag or git
> commit, sha256, and what was rejected — is in **`latex/PROVENANCE.md`**, with a
> per-venue copy in `latex/<venue>/PROVENANCE.txt`.
>
> **Current LaTeX entry for ECCV:** `latex/eccv/2026/kit/main.tex` (the 2026 kit
> supersedes `latex/eccv/kit/`, which is now historical). Chain of custody and
> sha256: **`latex/eccv/2026/SOURCE.md`** + `latex/eccv/2026/SHA256SUMS`.

**LaTeX kits verified by compilation.** All 11 that ship a buildable document were
compiled from a throwaway copy (`scripts/build_latex_kits.sh`), so `latex/` itself
stays byte-identical to what was downloaded:

| Kit | Result | Kit | Result |
|---|---|---|---|
| neurips 2025 | ✅ | acl | ✅ |
| icml 2026 | ✅ | aaai 2027 | ✅ |
| iclr 2027 | ✅ | ijcai 2026 | ✅ |
| cvpr 2026 | ✅ | ieee (IEEEtran conf) | ✅ |
| iccv 2025 | ✅ | acm `sigconf` (kdd/sigir/www) | ✅ |
| eccv 2022 *(historical)* | ✅ | | |

**11 compiled, 0 failed.** Details and logs: `BUILD_REPORT.md`. That record is the
2026-09-17 state and is left as it was; the ECCV row there is the superseded 2022
kit. The **ECCV 2026** kit was compiled separately on 2026-09-23 from a throwaway
copy (`scripts/build_latex_kits.sh --no-report eccv`, which now defaults to
`eccv/2026/kit/main.tex`): 15 pages, per-page `pdftotext -layout` identical to the
kit's own reference PDF (`latex/eccv/2026/SOURCE.md`, evidence
`/tmp/docs-three-kinds-20260923/eccv-report.md`). `BUILD_REPORT.md` was not
rewritten, by design.

---

## Typst template cards

### `bloated-neurips` 0.8.0

```
Venue: NeurIPS
Template: bloated-neurips 0.8.0 (@preview)
Format: Typst
Source: https://typst.app/universe/package/bloated-neurips
        upstream https://github.com/daskol/typst-templates  (MIT, © 2023 Daniel Bershatsky)
Official / Community: Community
Year: targets the NeurIPS 2026 style (calls `neurips2026.with(...)`)
Latest verified: 2026-09-17 — package published 2026-04-27; upstream last push 2026-05-10
Submission-safe: NO. NeurIPS accepts LaTeX only, via its own Styles.zip.
License: MIT
Notes: The most complete of the community set — ships a checklist, an appendix
       and rule helpers (toprule/midrule/botrule). Font stack already falls back
       through ("Times New Roman", "Nimbus Roman", "TeX Gyre Termes"), so it
       renders correctly without commercial fonts.
```

### `lucky-icml` 0.7.1 — **locally patched**

```
Venue: ICML
Template: lucky-icml 0.7.1 (@local, patched) / 0.7.0 (@preview, BROKEN on Typst 0.15)
Format: Typst
Source: https://github.com/daskol/typst-templates  (MIT, © 2023 Daniel Bershatsky)
Official / Community: Community
Year: targets ICML 2025 (also ships an icml2024 style)
Latest verified: 2026-09-17 — upstream last push 2026-05-10
Submission-safe: NO. Use latex/icml/ (icml2026.sty).
License: MIT
Notes: @preview/lucky-icml:0.7.0 does NOT compile on Typst 0.15.1 — see
       typst/icml/PATCHES.md for the one-line fix (an assert message that cannot
       be constructed). No upstream fix at the time of writing.
```

### `clear-iclr` 0.7.1 — **locally patched**

```
Venue: ICLR
Template: clear-iclr 0.7.1 (@local, patched) / 0.7.0 (@preview, demo broken)
Format: Typst
Source: https://github.com/daskol/typst-templates  (MIT, © 2023 Daniel Bershatsky)
Official / Community: Community
Year: targets ICLR 2026 (also ships iclr2025)
Latest verified: 2026-09-17 — upstream last push 2026-05-10
Submission-safe: NO. Use latex/iclr/ (iclr2027 kit from ICLR/Master-Template).
License: MIT
Notes: In @preview:clear-iclr:0.7.0 only the DEMO document is broken (Typst
       renamed the `diff` math shorthand to `dif`); the style library itself
       imports fine. See typst/iclr/PATCHES.md.
```

### `blind-cvpr` 0.7.0

```
Venue: CVPR
Template: blind-cvpr 0.7.0 (@preview)
Format: Typst
Source: https://typst.app/universe/package/blind-cvpr
        upstream https://github.com/daskol/typst-templates  (MIT)
Official / Community: Community
Year: targets CVPR 2025
Latest verified: 2026-09-17 — package published 2026-01-26
Submission-safe: NO. Use latex/cvpr/ (cvpr-org/author-kit, CVPR 2026).
License: MIT
Notes: Anonymous-review layout. Compiles clean; emits the most benign
       font-fallback warnings of the set.
```

### `tracl` 0.8.1

```
Venue: ACL, and by extension EMNLP / NAACL / EACL (they share the *ACL style files)
Template: tracl 0.8.1 (@preview)
Format: Typst
Source: https://typst.app/universe/package/tracl
        upstream https://github.com/coli-saar/tracl  (Apache-2.0)
Official / Community: Community — but authored by the Saarland University
        Computational Linguistics group, i.e. *ACL-adjacent, not a random port.
Year: current *ACL style (no year in the name)
Latest verified: 2026-09-17 — upstream last push 2026-01-27
Submission-safe: NO. ACL accepts LaTeX only.
License: Apache-2.0
Notes: API differs from the rest — see "API differences" below. Also needs
       pergamon for its bibliography plumbing.
```

### `charged-ieee` 0.1.4 / `bamdone-ieeeconf` 0.1.3

```
Venue: IEEE-style (generic)
Template: charged-ieee 0.1.4, bamdone-ieeeconf 0.1.3 (@preview)
Format: Typst
Source: https://github.com/typst/templates  (MIT-0) — maintained by the Typst
        project itself
Official / Community: Typst-official. NOT IEEE-official, and IEEE has no Typst
        acceptance path.
Year: no year; generic IEEE look
Latest verified: 2026-09-17 — repo last push 2026-03-20
Submission-safe: NO. Use latex/ieee/ (IEEEtran v1.8b).
License: MIT-0
Notes: The cleanest Typst API of the whole set (flat author list, no
       (authors, affils) tuple). Best default when you want an IEEE-ish look
       for an internal document.
```

### `ieee-vgtc` 0.0.4

```
Venue: IEEE VGTC conferences / TVCG journal
Template: ieee-vgtc 0.0.4 (@preview)
Format: Typst
Source: https://github.com/ieeevgtc/ieee-vgtc-typst  (MIT-0)
Official / Community: Community, but published under an IEEE VGTC-named GitHub
        org. Treat as unverified until VGTC itself says otherwise.
Year: current
Latest verified: 2026-09-17 — repo last push 2026-06-26
Submission-safe: NO — and note it is the only one of these with a plausible
        claim to organizational backing, so verify directly with VGTC.
License: MIT-0
```

### `classic-jmlr` 0.7.0 · `smooth-tmlr` 0.7.0

```
Venue: JMLR · TMLR
Format: Typst
Source: https://github.com/daskol/typst-templates  (MIT)
Official / Community: Community
Year: current
Latest verified: 2026-09-17 (packages published 2026-01-26)
Submission-safe: NO for JMLR (LaTeX). TMLR accepts a wide range of formats but
        check the current policy before relying on this.
License: MIT
```

### `magic-isprs` 0.1.0

```
Venue: ISPRS (photogrammetry / remote sensing)
Format: Typst
Source: https://github.com/alexandre-bry/ISPRS-Typst-Template  (MIT-0)
Official / Community: Community
Year: current
Latest verified: 2026-09-17 — repo last push 2026-05-10, 0 stars
Submission-safe: UNVERIFIED. Small single-author project; read it before trusting it.
License: MIT-0
```

### `generic-paper` 0.2.0 — **this library**

```
Venue: none
Format: Typst
Source: original work for this library (typst/generic/generic.typ, MIT,
        © 2026 Local template library)
Official / Community: neither — it is not a venue template at all
Year: —
Submission-safe: NO. It is not submission material for anything; it is the
        "no submission target decided yet" default for a paper draft.
License: MIT (you own it; modify freely)
0.2.0: layered starter added (typst/generic/starter/): main.typ + meta.typ +
        content/ (abstract loaded by meta.typ) + references.bib + assets/.
        Backward-compatible language parameters (lang / font / abstract-label /
        keywords-label) so a Chinese draft needs no template patch. The
        generic-paper(...) API of 0.1.0 keeps working.
```

### Layered document templates — **this library**

```
Daily entries:
  chinese-research      0.2.0   调研综述 (survey / review)
  modern-technical      0.2.0   工程技术文档 (engineering / technical document)
  generic-paper         0.2.0   paper draft, submission target not decided yet
Optional report layouts:
  academic-clean        0.1.0   greyscale, print-friendly
  chinese-thesis-report 0.1.0   long Chinese chapter-style report
Source: original work for this library (origin: own)
Official / Community: neither
Submission-safe: N/A — internal documents and drafts, not submissions
License: MIT (you own them)
```

All five are **layered projects**: `scripts/new_typst_paper.{sh,ps1}` generates
`main.typ` (assembly only) + `meta.typ` + `content/` + a frozen
`vendor/template/` snapshot + `template.lock` + `Makefile`. The generated project
carries the template source with it, so it needs **no** `@local`/`@preview`
package and no network. Each template keeps its own `starter/` skeleton under
`reports/<id>/starter/` (and `typst/generic/starter/`). Manifest rows whose path
starts with `reports/`, plus `generic-typst`, use the layered path and require
that starter; a missing starter fails before creating the project. Other rows
need an adapted venue entry in `examples/radar-paper/`. The shared
build/verify/README assets live once in `shared/report-project/`.

The three 0.2.0 starters wire the library's citation/figure conventions:
semantic `cite` + `bibliography` (superscript `[1]` in the prose, baseline `[1]`
in the bibliography), explicit `kind:` on figures/tables with stable labels,
table captions above and figure captions below. Each starter ships one **real**
bibliography entry (the Typst documentation, a typesetting demo — explicitly not
research evidence) and its own `assets/*.svg` diagrams, copied into the project
by the scaffolder.

`chinese-thesis-report` 0.1.0 is a **self-built** chapter-style technical report
template (A4 / 25 mm margins / cover + abstracts + TOC + notation + numbered
chapters + three-line tables). It follows the common Chinese thesis *layout*
conventions but is **NOT** any university's official degree-thesis template and
makes no compliance claim. For an actual degree submission, use your
university's current official template.

Not registered / not scaffolded: `reports/chinese-plain` and
`vendor/elegant-mono` stay in the library as assets but have no manifest row and
no starter, so the scaffolder refuses them by design (it never substitutes a
different template).

---

## Quality scores (1–5)

Scored by inspection of the rendered output and the upstream repository, not by
reputation.

| Template | Visual Quality | Maintainability | Completeness | Official Fidelity | Ease of Modification |
|---|:--:|:--:|:--:|:--:|:--:|
| `bloated-neurips` | 5 | 4 | 5 | 4 | 3 |
| `clear-iclr` | 4 | 4 | 4 | 4 | 3 |
| `lucky-icml` | 4 | 4 | 4 | 4 | 3 |
| `blind-cvpr` | 4 | 4 | 3 | 4 | 3 |
| `tracl` (ACL) | 4 | 3 | 3 | 5 | 2 |
| `charged-ieee` | 4 | 5 | 3 | 3 | 5 |
| `bamdone-ieeeconf` | 3 | 5 | 2 | 3 | 4 |
| `ieee-vgtc` | 4 | 4 | 4 | 4 | 3 |
| `classic-jmlr` | 4 | 4 | 4 | 4 | 3 |
| `smooth-tmlr` | 4 | 4 | 4 | 4 | 3 |
| `magic-isprs` | 3 | 2 | 3 | 3 | 3 |
| `generic-paper` (own) | 4 | 5 | 4 | — | 5 | 
| `modern-technical` (own) | 5 | 5 | 4 | — | 5 |
| `academic-clean` (own) | 4 | 5 | 4 | — | 5 |
| `chinese-research` (own) | 5 | 5 | 4 | — | 5 |
| `chinese-thesis-report` (own) | 5 | 5 | 4 | — | 4 |

*Official Fidelity* asks "how close is this to what the venue actually prints",
and is capped at 5 for `tracl` because it is built by an *ACL-adjacent group.
A high score here still does **not** mean the venue accepts it.

---

## API differences you will hit

These are real and are absorbed by the entry files / `_adapt.typ`, not by the body.

| Template | Author block | Citations | Equation numbering |
|---|---|---|---|
| `bloated-neurips`, `clear-iclr`, `lucky-icml`, `blind-cvpr` | `authors: (author-array, affiliation-dict)` | native `@key` | configurable |
| `charged-ieee`, `bamdone-ieeeconf` | flat array, one org per author | native `@key` | configurable |
| `tracl` | `make-authors((name:, affiliation: content), …)` | **`#cite("key")`**, not `@key` | **off by default** — `@eq:` fails until you enable it |
| `generic-paper` (own) | neutral schema, same as `content/_meta.typ` | native `@key` | on |
| `modern-technical`, `chinese-research` (own) | `(name:, affiliation:)` array | native `@key` | on |

0.2.0 language switches (backward compatible — the defaults reproduce 0.1.0):
`modern-technical` takes `lang` / `font` / `heading-font` / `toc-title`, and
`callout(..., label:)`; `generic-paper` takes `lang` / `font` / `abstract-label` /
`keywords-label`. The Chinese starter passes them; nothing is guessed from the CLI.
Default font lists in `modern-technical` now end with explicit Simplified-Chinese
families, because Typst's automatic fallback otherwise picks Japanese CJK fonts.

---

## Recommendations

### 日常写作：三个默认入口

1. **`chinese-research` 0.2.0** — 调研综述。中文长文：问题与范围、代表工作与机制、
   横向比较与证据、结论与开放问题；需要选型时在比较与结论里按约束给建议。
2. **`modern-technical` 0.2.0** — 工程技术文档。问题与约束、原理与方案、实现与接口、
   验证与限制；可选 callout，中文字体/语言走 `lang` / `font` 参数。
3. **`generic-paper` 0.2.0** — 投稿目标未定的论文草稿：引言、相关工作、方法或论证、
   结果与分析、结论。理论稿可用命题/证明替换实验；没有证据不要写贡献。

可选版式：`academic-clean`（黑白灰、打印友好）、`chinese-thesis-report`（长报告）。
会议风格模板（`bloated-neurips`、`clear-iclr`、`lucky-icml`、`blind-cvpr`、`tracl`、
`charged-ieee` 等）当**写作期的样式预览**用，不是投稿路径：选定目标之后，按目标
当年的官方要求组装，不要预设某个会议。`tracl` 只在你确实投 *ACL 系会议时再用，
它要求换一套引用语法。

### Venue submissions: check the target's current instructions

The master table above records the collection state per row (2026-09-17; the ECCV
row was re-verified online 2026-09-23) — for those venues the official artifact was
a LaTeX kit (or a publisher class such as ACM `acmart` / IEEEtran), and the Typst
packages were community look-alikes. Treat that as **dated evidence, not a standing
rule**: acceptance rules change every year, some venues accept custom or
Typst-based layouts, or a Word template of their own, and no venue other than ECCV
was checked after 2026-09-17. Before submitting, read the target's current-year
author instructions; when the venue ships its own kit, use `latex/<venue>/`:

NeurIPS · ICML · ICLR · CVPR · ICCV · ECCV · ACL · EMNLP · AAAI · IJCAI ·
KDD · SIGIR · TheWebConf · any IEEE conference or journal.

Special cases worth remembering:

- **ECCV** uses Springer **`llncs.cls`**, not `cvpr.sty`. Do not substitute. The
  current kit is `latex/eccv/2026/kit/` (2026, commit `da8c09c4`);
  `latex/eccv/kit/` is the 2022 kit kept purely as history. The 2026 submission
  page also offers a **Word** route (official Springer LNCS Word template), which
  this library does not store.
- **EMNLP** ships no kit of its own; it uses the ACL style files (byte-identical).
- **KDD / SIGIR / WWW** all use ACM **`acmart`** — one kit covers all three.
- **ICCV** has a dedicated author kit, separate from the CVPR one.
- **IEEE** on any venue: `IEEEtran`. For conferences use its conference option;
  for TGRS/GRSL/TAES/T-RS use the journal option.

### 可以放心长期用于技术报告

These are yours — no upstream can break them and there is no submission question.
All of them generate layered projects (vendor snapshot + lock) with the same
`-t` command:

- **`chinese-research` 0.2.0** — 调研综述（默认入口）；中文技术报告、评审材料。
- **`modern-technical` 0.2.0** — 工程技术文档（默认入口）；AI / Agent / Radar /
  AI4Science 报告与白皮书、设计说明。
- **`generic-paper` 0.2.0** — 未定投稿目标的论文草稿（默认入口）。
- **`academic-clean` 0.1.0** — formal research reports and surveys; greyscale, prints well.
- **`chinese-thesis-report` 0.1.0** — long Chinese chapter-style technical reports
  (cover / abstracts / TOC / notation / three-line tables). Self-built: **not** an
  official university thesis template.

---

## Known gaps and caveats

- **No Typst template exists** for ICCV, ECCV, AAAI, IJCAI, KDD, SIGIR, WWW or
  the IEEE Radar family. Those folders in `typst/` contain an explanation, not a
  fabricated template.
- **ECCV's LaTeX kit here is the 2026 one** (`latex/eccv/2026/kit/`, GitHub
  `paolo-favaro/paper-template` tag `Latest` @ commit `da8c09c4`; MIT per its own
  `LICENSE` © 2023 eccv26, while the bundled Springer LNCS components keep
  Springer's terms). Chain of custody: `latex/eccv/2026/SOURCE.md`; file hashes:
  `latex/eccv/2026/SHA256SUMS`. The 2022 kit (`latex/eccv/kit/`) stays as a
  historical record, and the 2026-09-17 entry in `BUILD_REPORT.md` still describes
  that 2022 compile — it was not rewritten.
  Historical note, kept as written on 2026-09-17: the ECCV 2024 site was
  unreachable throughout collection (`eccv2024.ecva.net` resolves but the host
  refused every connection after one transient success, proxy bypassed, ~20
  attempts), and no official ECCV GitHub org exists. The ECCV host answered on
  2026-09-23, which is why the row above is now current; the current page states
  the template has changed since ECCV 2024 and offers both a LaTeX kit and a
  Springer LNCS Word route.
- **IEEE's own template server was WAF-blocked** during collection, so the IEEE
  kit here is CTAN `IEEEtran` — which is exactly what RADAR 2026's author page
  points authors to, so this is the sanctioned path, not a workaround.
- **`@preview/lucky-icml:0.7.0` and `@preview/clear-iclr:0.7.0` do not compile on
  Typst 0.15.1.** Both were vendored and patched; see the two `PATCHES.md` files.
- The typst templates are community work. Their licenses are retained verbatim in
  `typst/<venue>/LICENSE`; nothing here is re-licensed or re-attributed.
