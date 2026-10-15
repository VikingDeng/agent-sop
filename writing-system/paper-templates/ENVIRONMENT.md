# ENVIRONMENT

What was actually found on this machine, what was installed, and how it was
verified. Everything below was probed live on **2026-09-17**; nothing here is
recalled from memory.

Reproduce at any time:

```bash
./scripts/check_environment.sh          # terminal report
./scripts/check_environment.sh --md     # markdown table
./scripts/check_environment.ps1         # same, PowerShell
```

---

## Machine

| Item | Value |
|---|---|
| OS | Ubuntu 26.04 LTS (Resolute Raccoon) |
| Kernel | Linux 7.0.0-31-generic, x86_64 |
| Working directory | `/home/viking/dev/projects/work` |
| Library root | `/home/viking/dev/docs/_shared/paper-templates`（2026-09-21 迁入 `docs/_shared/`；2026-09-17 本行探测值为 `/home/viking/dev/projects/work/paper-templates`，该旧路径现为兼容符号链接） |
| Disk free under `$HOME` | 340 GB |
| Passwordless sudo | **No** — every install below is user-level |

Filesystem layout note: `$HOME` is on `/dev/nvme1n1p3`. Because there is no
sudo, nothing was written to `/usr`, `/opt`, or `/etc` except through the
existing VS Code CLI.

---

## Before → after

### Already present

| Tool | Version | Path |
|---|---|---|
| VS Code | 1.137.0 | `/usr/bin/code` |
| `git` | 2.53.0 | `/usr/bin/git` |
| `python3` | 3.14.4 | `/usr/bin/python3` |
| `curl` / `wget` / `unzip` / `fc-list` | — | `/usr/bin` |
| LaTeX Workshop (VS Code ext) | 10.18.0 | pre-installed |

### Not present, installed during this setup

| Tool | Version | Installed to | Method |
|---|---|---|---|
| Typst CLI | **0.15.1** | `~/.local/bin/typst` | official GitHub release, musl static tarball |
| TinyTeX / TeX Live | **2026** | `~/.TinyTeX` | `TinyTeX-1-linux-x86_64-v2026.09.tar.xz` (51 MB) |
| Tinymist (VS Code ext) | **0.15.8** | `~/.vscode/extensions/` | VSIX from the Marketplace CDN |
| Tinymist (LSP binary) | 0.15.8 | `~/.local/bin/tinymist` | GitHub release, **glibc** build |
| Typst Companion (ext) | 0.0.6 | `~/.vscode/extensions/` | Marketplace |
| PowerShell | **7.6.6** | `~/.local/opt/powershell`, symlink in `~/.local/bin` | GitHub release tarball |
| TeX Gyre fonts | 33 faces | `~/.local/share/fonts/tex-gyre` | CTAN `tex-gyre.zip` |

### Present *after* (full tool table)

| Tool | Version | Path |
|---|---|---|
| `typst` | typst 0.15.1 (9dfd3a08) | `/home/viking/.local/bin/typst` |
| `tinymist` | 0.15.8 | `/home/viking/.local/bin/tinymist` |
| `xelatex` | XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026) | `~/.TinyTeX/bin/x86_64-linux/` |
| `lualatex` | LuaHBTeX 1.24.0 (TeX Live 2026) | `~/.TinyTeX/bin/x86_64-linux/` |
| `pdflatex` | pdfTeX 1.40.29 (TeX Live 2026) | `~/.TinyTeX/bin/x86_64-linux/` |
| `latexmk` | 4.88 | `~/.TinyTeX/bin/x86_64-linux/` |
| `tlmgr` | rev 79639 (2026-07-10) | `~/.TinyTeX/bin/x86_64-linux/` |
| `biber` | 2.22 | `~/.TinyTeX/bin/x86_64-linux/` |
| `bibtex` | BibTeX 0.99e | `~/.TinyTeX/bin/x86_64-linux/` |
| `pwsh` | 7.6.6 | `~/.local/bin/pwsh` |
| `git` | 2.53.0 | `/usr/bin/git` |
| `python3` | 3.14.4 | `/usr/bin/python3` |
| `code` | 1.137.0 | `/usr/bin/code` |

TeX Live package count after the bulk install: **~880 LaTeX packages**
(`collection-latexrecommended`, `-mathscience`, `-fontsrecommended`,
`-pictures`, `-langchinese`, `-bibtexextra`, plus the individual packages the
author kits need: `acmart`, `IEEEtran`, `sttools`, `oberdiek`, `upquote`,
`soul`, `cleveref`, `currfile`, `aliascnt`, `axessibility`, `accsupp`, …).

`biber` **was** missing from the TinyTeX-1 bundle and was installed explicitly.

---

## VS Code extensions relevant to writing

| Extension | ID | Version | Role |
|---|---|---|---|
| Tinymist Typst | `myriad-dreamin.tinymist` | 0.15.8 | Typst LSP, preview, formatter, linter |
| Typst Companion | `calebfiggers.typst-companion` | 0.0.6 | Markdown-like editing niceties on top of Tinymist |
| LaTeX Workshop | `james-yu.latex-workshop` | 10.18.0 | LaTeX build/preview for the official author kits |

The deprecated `typst-lsp` and `typst-preview` extensions were **not** installed:
Tinymist supersedes both and installing them alongside causes duplicate
language-server registration.

### Tinymist: one non-obvious problem, and the fix

The binary bundled **inside** the Tinymist VSIX is linked against the **musl**
loader:

```
$ file ~/.vscode/extensions/myriad-dreamin.tinymist-0.15.8/out/tinymist
ELF 64-bit LSB pie executable, x86-64, dynamically linked,
interpreter /lib/ld-musl-x86_64.so.1
```

A stock Ubuntu has no `/lib/ld-musl-x86_64.so.1`, so that binary cannot start —
it fails with `No such file or directory`, which reads like a missing file
rather than a missing loader. Installing the `musl` package would need sudo.

Fixed by installing the **glibc** build from the same upstream release
(`tinymist-linux-x64`, interpreter `/lib64/ld-linux-x86-64.so.2`, 77 MB) to
`~/.local/bin/tinymist` and pointing the extension at it:

```jsonc
"tinymist.serverPath": "${env:HOME}/.local/bin/tinymist"
```

Verified working on the library's own documents:

```
$ tinymist probe                      # exits clean
$ tinymist lint main-neurips.typ      # only the benign font-fallback warning
$ tinymist test main-icml.typ         # "Found 0 tests and 0 examples ... All test cases passed"
```

---

## Fonts

| Item | Count |
|---|---|
| CJK fonts installed | 89 |
| Noto Serif CJK SC | present (7 faces) |
| Noto Sans CJK SC | present (7 faces) |
| TeX Gyre faces | 33 |

The two CJK families that matter were **already present**, so the Chinese
report template works without installing anything.

**Added:** the full TeX Gyre family (33 OTF faces) from CTAN `tex-gyre.zip` into
`~/.local/share/fonts/tex-gyre`. These are the metric-compatible free
substitutes for Times / Palatino / Helvetica / Courier / Century Schoolbook.

**Also added:** `~/.config/fontconfig/fonts.conf`, a purely **additive** alias
layer mapping commercial font names onto those free equivalents:

```
Times New Roman → TeX Gyre Termes      Arial / Helvetica → TeX Gyre Heros
Courier New     → TeX Gyre Cursor      Palatino          → TeX Gyre Pagella
Book Antiqua    → TeX Gyre Bonum       Century Schoolbook → TeX Gyre Schola
Source Han Serif SC → Noto Serif CJK SC
```

A real commercial font, if you install one, still wins over these aliases.

### On the "unknown font family" warning

Templates request font *stacks*, e.g. ICML's
`("Times New Roman", "Nimbus Roman", "TeX Gyre Termes")`. Typst warns about each
name it cannot find and then uses the first one it can. So this warning is
**benign** and appears even on a fully working build.

What matters is what ends up embedded. Verified directly out of the produced PDFs:

| Document | Embedded fonts |
|---|---|
| ICML example | `NimbusRoman-Regular/Bold/Italic/BoldItalic`, `NewCMMath-Book` |
| `modern-technical` report | `NotoSans-Regular/Bold`, `NewCM10-Regular/Bold`, `NewCMMath`, `DejaVuSansMono` |
| `chinese-research` report | `NotoSerifCJKsc-Regular/Bold`, `NotoSansCJKsc-Regular/Bold/Black`, `NewCMMath` |

i.e. a Times-metric serif for ICML, the intended sans+serif pair for the
technical report, and genuine Source-Han-derived CJK for the Chinese one.

---

## Typst packages

| Item | Count |
|---|---|
| `@preview` packages cached | 16 |
| `@local` packages installed | 6 |

Typst keeps **two different directories**, which is a common source of confusion:

| Kind | Path | Holds |
|---|---|---|
| data dir | `~/.local/share/typst/packages` | `@local/…` — packages installed by hand |
| cache dir | `~/.cache/typst/packages` | `@preview/…` — downloaded from packages.typst.org |

The 6 `@local` packages are this library's own and patched templates, installed
by `scripts/install-local-typst-packages.sh`:

```
@local/lucky-icml:0.7.1        @local/generic-paper:0.1.0
@local/clear-iclr:0.7.1        @local/modern-technical:0.1.0
@local/academic-clean:0.1.0    @local/chinese-research:0.1.0
```

**Re-run that script after editing** `typst/icml`, `typst/iclr`, `typst/generic`
or anything under `reports/`, or the installed copy goes stale.

---

## PATH configuration

Two files were appended to, so both interactive shells and GUI-launched editors
find the new tools:

| File | Why |
|---|---|
| `~/.zshenv` | terminal sessions, VS Code tasks |
| `~/.config/environment.d/dev-toolchains.conf` | graphical session (an editor launched from the icon menu does not read `.zshenv`) |

Both received:

```sh
export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$HOME/.local/bin:$PATH"
```

**The `environment.d` change needs a re-login to take effect.** For the current
session without logging out:

```bash
systemctl --user set-environment PATH="$HOME/.TinyTeX/bin/x86_64-linux:$HOME/.local/bin:$PATH"
```

The library's scripts also set `PATH` themselves, so they work even in a shell
that has not picked the change up.

---

## Disk usage

| Path | Size |
|---|---|
| `~/.TinyTeX` | 829 MB |
| `~/.vscode/extensions/myriad-dreamin.tinymist-0.15.8` | 80 MB (of which 76 MB is the unusable musl binary) |
| `~/.local/opt/powershell` | ~290 MB |
| `paper-templates/` | 185 MB (of which ~56 MB is `latex/`) |

`latex/kdd`, `latex/sigir` and `latex/www` are byte-identical ACM kits and are
**hardlinked** to each other; likewise `latex/emnlp` → `latex/acl` and
`latex/radar` → `latex/ieee`. That is why 15 kits fit in 56 MB.

---

## Environment problems encountered (and what they were)

Recorded because they cost real time and are likely to recur.

1. **TinyTeX's own installer failed mid-download.** `yihui.org`'s install script
   died at 85 % with `curl: (56) OpenSSL SSL_read: unexpected eof while reading`.
   Switched to the GitHub-released, platform-specific
   `TinyTeX-1-linux-x86_64-v2026.09.tar.xz` (51 MB) instead of the 191 MB
   cross-platform bundle — it downloaded cleanly and is the better artifact anyway.
2. **The VS Code Marketplace CDN is slow from here.** `code --install-extension
   myriad-dreamin.tinymist` timed out at 400 s twice. Downloading the `.vsix`
   directly with `--retry` and installing from the file worked (34.5 MB).
3. **CTAN's default mirror 403'd** on some paths; `mirrors.ustc.edu.cn` served
   everything fast, and is now the configured `tlmgr` repository:
   `tlmgr option repository https://mirrors.ustc.edu.cn/CTAN/systems/texlive/tlnet`.
4. **`~/.config/fontconfig/` did not exist.** Created from scratch, so nothing
   of yours was overwritten.
5. **Tinymist's bundled binary needs musl** — see the section above.

Nothing else was modified. The library touches only: `~/.local/`,
`~/.TinyTeX/`, `~/.config/fontconfig/fonts.conf`,
`~/.config/environment.d/dev-toolchains.conf`, `~/.zshenv`, the Typst package
dirs, `~/.vscode/extensions/`, and `paper-templates/` itself.
