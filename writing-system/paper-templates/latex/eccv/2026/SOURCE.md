# Source record — ECCV 2026 Author Kit (LaTeX)

```
Venue: eccv
Kit: ECCV 2026 Author Kit for LaTeX (GitHub paolo-favaro/paper-template, tag Latest)
Source type: Official (the official ECCV 2026 conference page links it)
Official: yes
Year/version: 2026 (eccv.sty; \usepackage[review,year=2026,ID=*****]{eccv};
              bundled llncs.cls v2.22 [2022/09/05])
Retrieved: 2026-09-23 (UTC)
Archive: _original.tar.gz (655,781 B,
         sha256 94110f033e0d8407673c9879157b438b40830acb125a345412997aa45845dda7)
Unpacked: 2026/kit/ (14 files, hashes in SHA256SUMS)
Status: OK
```

## Chain of custody (all HTTP checks re-run 2026-09-23 UTC)

| Step | URL | Result |
|---|---|---|
| Official page | `https://eccv.ecva.net/Conferences/2026/SubmissionPolicies` | HTTP 200, `text/html`, 59,063 B. Raw HTML kept outside the repo at `/tmp/docs-three-kinds-20260923/eccv-official/SubmissionPolicies.html`, sha256 `9526037337a88f58739eaecc962f34dac39540e05425c1db9bd998472bac737e` |
| Page anchor "GitHub repository" | `https://github.com/paolo-favaro/paper-template` | Anchor target read from the page HTML. The `github.com` HTML page itself did not load from this network in this session (connect timeout, twice); repository identity was confirmed through the GitHub API instead: `repos/paolo-favaro/paper-template` → 200, description "ECCV 2026 paper template", homepage `eccv.ecva.net/Conferences/2026`, license MIT |
| Page anchor "TAR ball" | `https://github.com/paolo-favaro/paper-template/archive/refs/tags/Latest.tar.gz` | 302 → `https://codeload.github.com/paolo-favaro/paper-template/tar.gz/refs/tags/Latest`, HTTP 200, `application/x-gzip` |
| Tag → immutable commit | GitHub API `/repos/paolo-favaro/paper-template/git/ref/tags/Latest` | `refs/tags/Latest` = commit `da8c09c40239d5665757527e77388f4716a6564a` |
| Commit archive (cross-check) | `https://codeload.github.com/paolo-favaro/paper-template/tar.gz/da8c09c40239d5665757527e77388f4716a6564a` | HTTP 200, 655,836 B; extracted content is per-file identical to the tag archive. Only the gzip container differs: its embedded top-level directory is `paper-template-da8c09c…/` instead of `paper-template-Latest/` |

The page states verbatim: *"Note also that the template has changed since ECCV 2024.
Authors must thus use this new template instead of templates from older conferences."*
It also says the kit can be obtained by cloning an Overleaf project, cloning/forking
the GitHub repository, or downloading a ZIP file or a TAR ball.

## License and origin of the code

- `kit/LICENSE` is the pack's own license, quoted verbatim in its first lines:
  `MIT License` / `Copyright (c) 2023 eccv26`. It covers the ECCV-authored files
  (`main.tex`, `main.bib`, `eccv.sty`, `eccvabbrv.sty`, `README.md`).
- The same pack redistributes **Springer LNCS** components: `llncs.cls`
  (`\ProvidesClass{llncs}[2022/09/05 v2.22]`), `splncs04.bst`, `llncsdoc.pdf`,
  `lncs_readme.txt`, `lncs_history.txt`, plus the sample figure `eijkel2.eps`/`.pdf`.
  Those keep Springer's own terms; the pack's MIT notice does not replace them.
- The library claims no copyright in this material. Files are stored verbatim, all
  upstream license/readme files are kept, and nothing (no local notes, no build
  intermediate) is ever written into `kit/`.

## Difference from the 2022 kit kept in `../kit/` (historical only)

| | 2022 (`../kit/`) | 2026 (`2026/kit/`) |
|---|---|---|
| Distribution | Google Drive ZIP from the ECCV 2022 call for papers | GitHub `paolo-favaro/paper-template`, tag `Latest` (commit `da8c09c…`) |
| Entry file | `eccv2022submission.tex` | `main.tex` |
| Bibliography | `egbib.bib` | `main.bib` |
| ECCV style | macros inline in the entry file, plus `comment.sty`, `ruler.sty` | separate packages `eccv.sty` + `eccvabbrv.sty` with `year=2026` / `review` options |
| LNCS class | `llncs.cls` v2.20 [2018/03/10] | `llncs.cls` v2.22 [2022/09/05] |
| License file | none in the pack | `LICENSE` (MIT, (c) 2023 eccv26) + `README.md` |
| Fit for ECCV 2026 | no — older template, per the page text above | yes |

The pre-existing retrieval records (`../PROVENANCE.txt`, `../../PROVENANCE.md`) describe
the 2022 download and are deliberately left untouched.

## Verification scope

- Re-fetched 2026-09-23: the official page, the tag→commit API answer, the repo
  metadata API answer, and the immutable-commit tarball (to cross-check the
  stored `_original.tar.gz` per file).
- Reachability note: `eccv.ecva.net`, `api.github.com` and `codeload.github.com`
  answered; `github.com` HTML pages timed out (connect timeout) from this network
  during this session, so no HTTP status is claimed for the repo web page.
- Not re-fetched: the ZIP and the Overleaf forms of the same kit (equivalent
  distributions named on the same page), and the rebuttal template.
- Integrity: `gzip -t` OK; `tar -tzf` lists 1 directory + 14 files; the unpacked
  `kit/` file set equals the archive's top-level file set;
  `sha256sum -c SHA256SUMS` passes from this directory.
- Build: compiled from a throwaway copy (never in place) by
  `scripts/build_latex_kits.sh`; `kit/` stays byte-identical to the archive.
