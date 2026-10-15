# LaTeX Author Kit Provenance Record

Official LaTeX author kits / style files for 15 academic venues, downloaded and verified.

- **Retrieved (all):** 2026-09-17 (UTC)
- **Staging root:** `/home/viking/dev/projects/work/paper-templates/.staging/latex/`
- **Rule applied:** official sources only (conference site, official GitHub org, publisher, CTAN). No blog / personal-site / aggregator templates were used, and no community template was ever substituted for an official one.
- **Verification:** every archive was checked for non-zero size, real zip/tar magic (no HTML error pages saved as `.zip`), `unzip -t` / `tar tzf` integrity, and presence of key `.cls` / `.sty` / `.tex` files.

---

## Venue records

```
Venue: neurips
Kit: NeurIPS 2025 Style Files (Styles.zip)
Source URL: https://media.neurips.cc/Conferences/NeurIPS2025/Styles.zip
Source type: Official conference site
Official: yes
Year/version: 2025 (neurips_2025.sty [2025/05/01])
Retrieved: 2026-09-17
Commit/ETag: ETag "801ff089006d4c30-2df71-634f31186ad00" (Last-Modified 2025-05-12)
Archive: _original.zip (188,273 B, sha256 72032130232955b785cd622b7c52d893e3166f30a90e1e6279d0a28e8373beef)
Unpacked: neurips/Styles/
Contains: neurips_2025.sty, neurips_2025.tex, neurips_2025.pdf
Status: OK
Notes: neurips.cc/Conferences/<year>/PaperInformation/StyleFiles is login-gated (404 -> /accounts/login?nextp=...), so media.neurips.cc is the public distribution point for the same official kit. NeurIPS2026/Styles.zip does not exist (HTTP 404); NeurIPS2024 (186,748 B) and NeurIPS2025 (188,273 B) do, so 2025 is the most recent. Build with pdflatex.
```

```
Venue: icml
Kit: ICML 2026 Style Files (icml2026.zip)
Source URL: https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip
Source type: Official conference site
Official: yes
Year/version: 2026 (icml2026.sty v2.0 [2025/10/29])
Retrieved: 2026-09-17
Commit/ETag: ETag "801ff08900116193-37c10-6437c315629c0" (Last-Modified 2025-11-13)
Archive: _original.zip (228,368 B, sha256 8b29290f5828e176debb57ea9cc00252502973d55ea561a2f18a7f0a326bfc6c)
Unpacked: icml/kit/
Contains: icml2026.sty, icml2026.bst, example_paper.tex, example_paper.bib, example_paper.pdf, algorithm.sty, algorithmic.sty, fancyhdr.sty, icml_numpapers.pdf
Status: OK
Notes: Discovery path: https://icml.cc/Conferences/2026/AuthorInstructions (the human-facing /StyleFiles page is login-gated, same as NeurIPS). The AuthorInstructions page links the media.icml.cc zip directly. There is no official ICML GitHub org (github.com/icml-org and github.com/ICML both 404), so this CDN zip is the authoritative artifact. No support for non-LaTeX typesetting; submissions must be anonymized. Build with pdflatex.
```

```
Venue: iclr
Kit: ICLR Master-Template (contains the iclr2027 author kit, plus iclr2026 / iclr2025 / older years)
Source URL: https://github.com/ICLR/Master-Template/archive/46ed6f4c6cef5b175dde23639e77d44c3463b230.tar.gz
Source type: Official GitHub org
Official: yes
Year/version: 2027 (iclr2027_conference.sty; repo also ships iclr2026, iclr2025, iclr2024.zip, iclr2023.zip, iclr2022.zip, iclr2020/, iclr2021/, archive/)
Retrieved: 2026-09-17
Commit/ETag: 46ed6f4c6cef5b175dde23639e77d44c3463b230 (branch master)
Archive: _original.tar.gz (2,673,233 B, sha256 f27c72e24f8dcb91f8ab2db3cacc8ca15114a061102edcc03ed0539c0faec684)
Unpacked: iclr/kit/
Contains: iclr2027/iclr2027_conference.sty, iclr2027_conference.bst, iclr2027_conference.tex, iclr2027_conference.bib, natbib.sty, fancyhdr.sty, math_commands.tex (and identical file sets under iclr2026/, iclr2025/); top level also has iclr2019_conference.sty/.bst/.tex, natbib.sty, fancyhdr.sty, math_commands.tex
Status: OK
Notes: IMPORTANT CORRECTION to the task brief: repositories named ICLR/iclr20XX do NOT exist. github.com/ICLR/iclr2024, iclr2025, iclr2026 and iclr2027 all return HTTP 404 "Not Found". The ICLR GitHub org publishes EVERY year from one repo: ICLR/Master-Template (default branch "master"). Use iclr2027/ as the current kit. There is no .zip for iclr2027 alone inside the repo, but iclr2022..iclr2024 do ship as year zips alongside the unpacked directories.
```

```
Venue: cvpr
Kit: CVPR/ICCV/3DV official author kit (updated for CVPR 2026)
Source URL: https://github.com/cvpr-org/author-kit/archive/291758547e923160eb4d37079b7b9f0dfce82355.tar.gz
Source type: Official GitHub org
Official: yes
Year/version: 2026 (cvpr.sty [2026 LaTeX class for IEEE CVPR])
Retrieved: 2026-09-17
Commit/ETag: 291758547e923160eb4d37079b7b9f0dfce82355 (branch main)
Archive: _original.tar.gz (24,496 B, sha256 106adc4fcac8ef7525fc99adc2630afba588b7670ffcf3ea0c8e46c25203da34)
Unpacked: cvpr/kit/
Contains: cvpr.sty, main.tex, preamble.tex, rebuttal.tex, main.bib, ieeenat_fullname.bst, sec/ (0_abstract, 1_intro, 2_formatting, 3_finalcopy, X_suppl), fig/teaser.tex, .github/workflows/latex-build.yml, README.md
Status: OK
Notes: Repo README titles this "Official LaTeX template for CVPR/ICCV/3DV", so this single repo also serves ICCV and 3DV. The CVPR 2026 MS Word template is no longer supported. Latest GitHub release tag is "CVPR2026-v1(latex)" (published 2025-09-17); the repo has only two repos in the org (author-kit, author-kit-msword), so there is no separate ICCV-only repo here. Submitted via the CVF paper site.
```

```
Venue: iccv
Kit: ICCV 2025 Author Kit (February revision)
Source URL: https://media.eventhosts.cc/Conferences/ICCV2025/ICCV2025-Author-Kit-Feb.zip
Source type: Official conference site
Official: yes
Year/version: 2025 (iccv.sty [2025 LaTeX class for IEEE ICCV])
Retrieved: 2026-09-17
Commit/ETag: ETag "801ff08900328f02-829f-62d404fd85b40" (Last-Modified 2025-02-03)
Archive: _original.zip (33,439 B, sha256 22c1bee4cf64c2106b9afaecf18807be9f8350a60576bc4bf4ba14a50ca36d83)
Unpacked: iccv/kit/
Contains: iccv.sty, main.tex, preamble.tex, rebuttal.tex, main.bib, ieeenat_fullname.bst, sec/ (0_abstract, 1_intro, 2_formatting, 3_finalcopy), README.md
Status: OK
Notes: There IS a dedicated ICCV kit, contrary to the assumption that ICCV only borrows the CVPR repo. It was linked from ICCV's own author-guidelines page at https://iccv.thecvf.com/Conferences/2025/AuthorGuidelines (found via the "AuthorGuidelines" page of the official CVF-hosted ICCV 2025 site), and is served from CVF's media host media.eventhosts.cc. main.tex declares \def\confName{ICCV}, \def\confYear{2025}, and selects the review/camera-ready variant via \usepackage[review]{iccv}. Note the archive also contained macOS junk (__MACOSX/, .DS_Store) which was removed on unpack. ICCV is additionally covered by cvpr-org/author-kit (see cvpr).
```

```
Venue: eccv
Kit: ECCV 2022 Author Kit (eccv2022AuthorKit.zip)
Source URL: https://drive.google.com/uc?export=download&id=171-xo72Jx40cZ4qT20ZZsDDKXPIOWnss
Source type: Official conference site
Official: yes
Year/version: 2022 (llncs.cls v2.20 [2018/03/10]; splncs04.bst)
Retrieved: 2026-09-17
Commit/ETag: - (Google Drive; no ETag. Drive file id 171-xo72Jx40cZ4qT20ZZsDDKXPIOWnss)
Archive: _original.zip (240,506 B, sha256 a2822fe9506bae0f45b777707edf0f5c40164b46dc0d2f84a97535e358e3c489)
Unpacked: eccv/kit/
Contains: llncs.cls, splncs04.bst, eccv2022submission.tex, comment.sty, ruler.sty, egbib.bib, llncsdoc.pdf, README.txt, history.txt, eijkel2.eps, eijkel2.pdf
Status: PARTIAL
Notes: The bytes come from Google Drive, but the link is the official one published by the ECCV organisers on the official ECCV 2022 Call for Papers page (https://eccv2022.ecva.net/submission/call-for-papers/), which lists "LaTeX Templates (zip): eccv2022AuthorKit.zip" and "LaTeX Templates (tar): eccv2022AuthorKit.tgz" pointing at those Drive files. Status is PARTIAL, not OK, because this is the 2022 kit rather than the most recent ECCV: the ECCV 2024 site (eccv2024.ecva.net, and the eccv.ecva.net alias) is UNREACHABLE from this network for the whole session (DNS resolves to 198.202.70.65 weber.snl.salk.edu; every request after one transient early 200 ended in connection-closed / "TLS alert decode error / unexpected eof while reading", both through the local proxy and with --noproxy, over ~20 attempts including a 10x8s retry loop). eccv2026.ecva.net does not resolve/connect. No official ECCV GitHub org exists: github.com/eccv-org, github.com/ECVA and github.com/cvpr-org/eccv-author-kit all return 404, and media.eventhosts.cc/Conferences/ECCV2024/ exists but common kit filenames there 404. IMPORTANT: ECCV uses the SPRINGER LNCS class (llncs.cls + splncs04.bst) and NOT the cvpr.sty family used by CVPR/ICCV — do not substitute the CVPR kit. Also note eccv.org is an unrelated Colorado water-sanitation district, NOT the conference; do not use it. The kit's own README.txt is stale and still refers to "eccv2020submission" although the shipped file is eccv2022submission.tex.
```

```
Venue: acl
Kit: *ACL official style files (acl-org/acl-style-files)
Source URL: https://github.com/acl-org/acl-style-files/archive/d5adc823ff0f80f98c80405ca0ab66c68e684409.tar.gz
Source type: Official GitHub org
Official: yes
Year/version: current master (no year in filename; latest *ACL rolling style files)
Retrieved: 2026-09-17
Commit/ETag: d5adc823ff0f80f98c80405ca0ab66c68e684409 (branch master)
Archive: _original.tar.gz (32,736 B, sha256 00977b20fce2795778298af837bd51dc0e9fd69e734c1b70742201e7ba08b34f)
Unpacked: acl/kit/
Contains: acl.sty, acl_natbib.bst, acl_latex.tex, acl_lualatex.tex, formatting.md, anthology.bib.txt, custom.bib, README.md, tests/regression/run_tests.py, .github/workflows/tests.yml
Status: OK
Notes: Repo description: "Official style files for papers submitted to venues of the Association for Computational Linguistics". acl_latex.tex is the pdfLaTeX template, acl_lualatex.tex is for XeLaTeX/LuaLaTeX. Authors may not modify these files or use another conference's template. The README also advertises an official Overleaf template (https://www.overleaf.com/latex/templates/association-for-computational-linguistics-acl-conference/jvxskxpnznfj) and a master.zip, but the archive above is the downloadable artifact.
```

```
Venue: emnlp
Kit: The *ACL style files (acl-org/acl-style-files) — EMNLP has no separate style kit
Source URL: https://github.com/acl-org/acl-style-files/archive/d5adc823ff0f80f98c80405ca0ab66c68e684409.tar.gz
Source type: Official GitHub org
Official: yes
Year/version: current master (shared *ACL style files)
Retrieved: 2026-09-17
Commit/ETag: d5adc823ff0f80f98c80405ca0ab66c68e684409 (branch master)
Archive: _original.tar.gz (32,736 B, sha256 00977b20fce2795778298af837bd51dc0e9fd69e734c1b70742201e7ba08b34f)
Unpacked: emnlp/kit/
Contains: acl.sty, acl_natbib.bst, acl_latex.tex, acl_lualatex.tex, formatting.md, anthology.bib.txt, custom.bib, README.md, tests/
Status: OK
Notes: SHARED LINEAGE WITH ACL — the archive here is byte-identical to the acl/ one (same sha256 00977b20...), which is expected and correct. Evidence of the official route: the official EMNLP 2025 calls page https://2025.emnlp.org/calls/main_conference_papers/ directs authors to ACL Rolling Review (https://aclrollingreview.org/cfp), whose guidelines state "Paper submissions must use the official ACL style template" and link https://github.com/acl-org/acl-style-files. No EMNLP-specific .sty exists. Caveat: https://2025.emnlp.org/ also links https://github.com/acl-org/emnlp-2025, but that repo is the conference WEBSITE (a Jekyll site: _pages/, _sass/, _includes/, downloads/, _config.yml), NOT style files — it was checked and rejected as a kit source. EMNLP also requires the ACL/ARR submission checklist.
```

```
Venue: aaai
Kit: AAAI-27 Author Kit (AuthorKit27)
Source URL: https://aaai.org/authorkit27/
Source type: Official conference site
Official: yes
Year/version: 2027 (aaai2027.sty [2027/05/04 AAAI 2027 Submission format])
Retrieved: 2026-09-17
Commit/ETag: ETag "6a18653c-53daef" (Last-Modified 2026-05-28)
Archive: _original.zip (5,495,535 B, sha256 e28c6ac9bc6eb3b4e2d849547d2cefb5162610ee39d0a12e0dc62d1126b44a7d)
Unpacked: aaai/kit/
Contains: aaai2027.sty, aaai2027.bst, aaai2027.bib, CameraReady2027.tex (+.pdf), AnonymousSubmission2027.tex (+.pdf), ReproducibilityChecklist.tex (+.pdf), Figures/figure1.pdf, Figures/figure2.pdf, Word/ (CameraReady2027.docx, AnonymousSubmission2027.docx, ReproducibilityChecklist.docx + .pdfs)
Status: OK
Notes: The URL looks like a web page but serves application/zip directly (Content-Type: application/zip), so it must be saved as a file, not parsed as HTML. The link is the one published on the official AAAI-27 conference page https://aaai.org/conference/aaai/aaai-27/. Caveat: this was a large (~5.5 MB) download and a naive short-timeout fetch truncates it mid-stream (a first attempt returned only 105 KB); it needs a generous --max-time (~90 s observed here). Includes both LaTeX and Word templates plus the reproducibility checklist.
```

```
Venue: ijcai
Kit: IJCAI-ECAI 2026 Formatting Guidelines (author kit)
Source URL: https://www.ijcai.org/sites/default/files/Guidelines/FormattingGuidelines-IJCAI-ECAI-26.zip
Source type: Official conference site
Official: yes
Year/version: 2026 (ijcai26.sty, ijcai26.tex)
Retrieved: 2026-09-17
Commit/ETag: - (no ETag; Last-Modified 2025-12-02 15:09:12 GMT)
Archive: _original.zip (69,002 B, sha256 68c0f282c3b2340795642586998dff19597686c4b34d0bd9057de43d4e2a6ed3)
Unpacked: ijcai/kit/
Contains: ijcai26.sty, ijcai26.tex, ijcai26.bib, named.bst, ijcai26.docx
Status: OK
Notes: Linked from the official IJCAI Author's Kit page https://www.ijcai.org/authors_kit ("You can download the IJCAI-ECAI 2026 formatting guidelines here"). Ships both LaTeX and Word templates. The archive's top-level directory is FormattingGuidelines-IJCAI-ECAI-26/ (renamed to kit/ locally for consistency).
```

```
Venue: kdd
Kit: ACM Primary Article Template — acmart v2.20 (SIGKDD has no separate LaTeX kit)
Source URL: https://portalparts.acm.org/hippo/latex_templates/acmart-primary.zip
Source type: Publisher
Official: yes
Year/version: acmart.cls v2.20 [2026/08/16]; ACM page states "last update June 28, 2026"
Retrieved: 2026-09-17
Commit/ETag: 4ac4814f8736276e0b6540679e5ed45a38231c40 (git commit hash embedded as the zip archive comment)
Archive: _original.zip (15,543,267 B, sha256 ad3489a190f35b99a6796d0c9895727546a5eae2dd8155ea00e97a991d6910ff)
Unpacked: kdd/acmart-primary/
Contains: acmart.cls (121,874 B, PRE-BUILT), acmart.dtx, acmart.ins, acmart.bib, ACM-Reference-Format.bst, acmauthoryear.bbx/.cbx, acmnumeric.bbx/.cbx, acmdatamodel.dbx, acmguide.pdf, acmart.pdf, LICENSE, README, Makefile, samples/ (sigconf.tex, sigplan.tex, acmsmall-submission.tex, acmlarge.tex, acmtog.tex, acmmanuscript.tex, acmengage.tex, ...)
Status: OK
Notes: ACM's OWN download, not CTAN — and it is the better artifact, because it contains a READY-TO-USE acmart.cls. Found on the official ACM page https://www.acm.org/publications/proceedings-template ("acmart.cls, the official ACM Primary article template for LaTeX... LaTeX (Version 2.20)"), which had to be read through the browser because direct curl to www.acm.org returns HTTP 403 (Cloudflare); the zip itself also 403s to curl even with a matching Referer/UA, so it was fetched with the browser session. KDD/SIGKDD publishes no LaTeX class of its own; ACM proceedings papers use acmart in sigconf mode. IF YOU PREFER CTAN: https://mirrors.ctan.org/macros/latex/contrib/acmart.zip — but note two things: (a) mirrors.ctan.org itself returned HTTP 403 for acmart.zip in this session while https://mirrors.mit.edu/CTAN/macros/latex/contrib/acmart.zip worked (15,106,903 B); and (b) the CTAN zip does NOT contain acmart.cls — it ships only acmart.dtx + acmart.ins, so you must run `latex acmart.ins` to generate the class (not possible here: no TeX is installed on this machine). The ACM portalparts zip avoids that step entirely. There is no official ACM template repo on GitHub: the github.com/acm-org org exists but has 0 public repositories. Requires the libertine font set; use only ACM-whitelisted LaTeX packages.
```

```
Venue: sigir
Kit: ACM Primary Article Template — acmart v2.20 (ACM SIGIR uses acmart; no separate kit)
Source URL: https://portalparts.acm.org/hippo/latex_templates/acmart-primary.zip
Source type: Publisher
Official: yes
Year/version: acmart.cls v2.20 [2026/08/16]
Retrieved: 2026-09-17
Commit/ETag: 4ac4814f8736276e0b6540679e5ed45a38231c40 (zip archive comment)
Archive: _original.zip (15,543,267 B, sha256 ad3489a190f35b99a6796d0c9895727546a5eae2dd8155ea00e97a991d6910ff)
Unpacked: sigir/acmart-primary/
Contains: acmart.cls, acmart.dtx, acmart.ins, acmart.bib, ACM-Reference-Format.bst, acmauthoryear.*, acmnumeric.*, samples/ (sigconf.tex et al.), acmguide.pdf, acmart.pdf, LICENSE, README, Makefile
Status: OK
Notes: Same situation and same artifact as kdd — ACM proceedings (SIGIR is an ACM SIG conference) use the ACM Primary Article Template / acmart in sigconf mode; there is no SIGIR-specific LaTeX class. Byte-identical archive to kdd/ and www/ (sha256 ad3489a1...); if disk space matters, keep one copy and symlink/hardlink the other two, since the files are duplicates by construction. Direct curl is blocked (403) — fetched via the browser session. See the kdd Notes for the CTAN alternative and its acmart.cls caveat.
```

```
Venue: www
Kit: ACM Primary Article Template — acmart v2.20 (The Web Conference is ACM; no separate kit)
Source URL: https://portalparts.acm.org/hippo/latex_templates/acmart-primary.zip
Source type: Publisher
Official: yes
Year/version: acmart.cls v2.20 [2026/08/16]
Retrieved: 2026-09-17
Commit/ETag: 4ac4814f8736276e0b6540679e5ed45a38231c40 (zip archive comment)
Archive: _original.zip (15,543,267 B, sha256 ad3489a190f35b99a6796d0c9895727546a5eae2dd8155ea00e97a991d6910ff)
Unpacked: www/acmart-primary/
Contains: acmart.cls, acmart.dtx, acmart.ins, acmart.bib, ACM-Reference-Format.bst, acmauthoryear.*, acmnumeric.*, samples/ (sigconf.tex et al.), acmguide.pdf, acmart.pdf, LICENSE, README, Makefile
Status: OK
Notes: The Web Conference (WWW) is ACM-published and follows the same ACM proceedings format, so the ACM Primary Article Template is the official kit — The Web Conference does not ship a bespoke LaTeX class. Byte-identical archive to kdd/ and sigir/ (sha256 ad3489a1...). Direct curl is blocked (403) — fetched via the browser session. See the kdd Notes for the CTAN alternative and its acmart.cls caveat.
```

```
Venue: ieee
Kit: IEEEtran document class + IEEE conference skeleton (IEEEtran.zip)
Source URL: https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip
Source type: CTAN
Official: yes
Year/version: CTAN package IEEEtran 1.8b (LPPL 1.3); IEEEtran.cls [2015/08/26 V1.8b by Michael Shell]
Retrieved: 2026-09-17
Commit/ETag: - (no ETag; archive member timestamps 2015-08-26/27)
Archive: _original.zip (1,727,001 B, sha256 e0cd4f5afbd42c8076092280e72b3e0a5111efe501d35de9f715cfb8da313cb4)
Unpacked: ieee/IEEEtran/
Contains: IEEEtran.cls, bare_conf.tex (conference skeleton), bare_conf_compsoc.tex, bare_jrnl.tex, bare_jrnl_compsoc.tex, bare_jrnl_compsoc.tex, bare_jrnl_comsoc.tex, bare_jrnl_transmag.tex, bare_adv.tex, bibtex/IEEEtran.bst (+IEEEtranS/N/SA/SN.bst), tools/IEEEtrantools.sty, testflow/testflow.tex
Status: OK
Notes: CTAN IEEEtran is IEEE-endorsed and is exactly what IEEE-sponsored conferences tell authors to use (see the radar record). ENVIRONMENTAL LIMITATION: IEEE's canonical "Conference Template" page https://www.ieee.org/conferences/publishing/templates.html is entirely blocked from this network by AWS WAF — it returns HTTP 202 with a zero-length body and the JS challenge "window.awsWafCookie...", and both curl (with realistic UA/Accept headers) and the shared browser get "The requested URL was rejected. Please consult with your administrator. Your support ID is: <nnn>". The direct DAM asset https://www.ieee.org/content/dam/ieee-org/ieee/web/org/conferences/conference-latex-template_10-17-19.zip is blocked the same way (202, 0 bytes), so the IEEE-hosted Word/LaTeX bundle could not be retrieved from here. Also blocked: https://template-selector.ieee.org/. What IS reachable is the IEEE Author Center, which routes users to the blocked page: https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/authoring-tools-and-templates/ (and the journal-side equivalent https://journals.ieeeauthorcenter.ieee.org/.../ieee-article-templates/), plus https://latexqc.ieee.org/ (IEEE LaTeX validation). CAUTION: the Overleaf template "Preparation of Papers for IEEE Sponsored Conferences and Symposia" (https://www.overleaf.com/latex/templates/preparation-of-papers-for-ieee-sponsored-conferences-and-symposia/zfnqfzzzxghk) is USER-SUBMITTED ("submitted by an author", last touched ~7 years ago, License: "Other (as stated in the work)") — it is NOT an IEEE-published template and was deliberately not used.
```

```
Venue: radar
Kit: IEEEtran used in "conference" mode (bare_conf.tex) — the format RADAR 2026 officially mandates
Source URL: https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip
Source type: CTAN
Official: yes
Year/version: CTAN package IEEEtran 1.8b; IEEEtran.cls [2015/08/26 V1.8b by Michael Shell]. RADAR 2026 official: https://2026.ieee-radarconf.org/
Retrieved: 2026-09-17
Commit/ETag: - (same artifact as the ieee venue)
Archive: _original.zip (1,727,001 B, sha256 e0cd4f5afbd42c8076092280e72b3e0a5111efe501d35de9f715cfb8da313cb4)
Unpacked: radar/IEEEtran/
Contains: IEEEtran.cls, bare_conf.tex, bare_conf_compsoc.tex, bare_jrnl*.tex, bibtex/IEEEtran.bst, tools/IEEEtrantools.sty, testflow/
Status: OK
Notes: Primary evidence, from the official RADAR 2026 submission system's "Samples and Templates" page (https://epapers2.org/radar2026/ESR/samples.php, linked from the official conference site https://2026.ieee-radarconf.org/): "In order to prepare a submission using LaTeX, please use the IEEEtran document class file in 'conference' mode. The most up to date distribution of such class is available either from the IEEE or the Comprehensive TeX Archive Network: IEEE Download Site | CTAN Site." That page links http://mirrors.ctan.org/macros/latex/contrib/IEEEtran/bare_conf.tex, i.e. exactly the bare_conf.tex shipped here, and also supplies MS Word templates, IEEE PDF eXpress, and the copyright form. The official conference author pages are https://2026.ieee-radarconf.org/authors/initial-author-instructions-0 (US Letter or A4; max 6 pages incl. figures/tables/references; no page numbers; embed all fonts; avoid Type 3; <=5 MB PDF) and .../final-author-instructions. SECONDARY CHECKS AS REQUESTED: (a) IEEE GRSS — https://www.grss-ieee.org/ is reachable and its IEEE Transactions on Radar Systems page https://www.grss-ieee.org/publications/ieee-transactions-on-radar-systems/ was inspected; GRSS publishes no GRSS-specific LaTeX template and instead routes authors to the IEEE Author Center (journals.ieeeauthorcenter.ieee.org) and IEEE Xplore publishing policies, consistent with IEEEtran being the class. (b) IEEE Transactions on Radar Systems has NO separate official template page — as an IEEE journal it uses the standard IEEE journal templates (IEEEtran + bare_jrnl.tex) from the IEEE Author Center. Note https://radar.ieee.org/ is dead (connection failure, HTTP 000), so radarconf sites must be located via search. Also relevant: IGARSS, TGRS, GRSL and TAES are all IEEE GRSS/AESS publications and likewise use IEEEtran.
```

---

## Summary table

| Venue | Status | Kit | Source | Official |
|---|---|---|---|---|
| neurips | OK | NeurIPS 2025 Style Files | https://media.neurips.cc/Conferences/NeurIPS2025/Styles.zip | yes |
| icml | OK | ICML 2026 Style Files | https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip | yes |
| iclr | OK | ICLR Master-Template (iclr2027) | https://github.com/ICLR/Master-Template | yes |
| cvpr | OK | CVPR/ICCV/3DV author kit (CVPR 2026) | https://github.com/cvpr-org/author-kit | yes |
| iccv | OK | ICCV 2025 Author Kit (Feb) | https://media.eventhosts.cc/Conferences/ICCV2025/ICCV2025-Author-Kit-Feb.zip | yes |
| eccv | PARTIAL | ECCV 2022 Author Kit | https://eccv2022.ecva.net/submission/call-for-papers/ (kit on Google Drive) | yes |
| acl | OK | *ACL style files | https://github.com/acl-org/acl-style-files | yes |
| emnlp | OK | *ACL style files (shared with ACL) | https://github.com/acl-org/acl-style-files | yes |
| aaai | OK | AAAI-27 Author Kit | https://aaai.org/authorkit27/ | yes |
| ijcai | OK | IJCAI-ECAI 2026 Formatting Guidelines | https://www.ijcai.org/sites/default/files/Guidelines/FormattingGuidelines-IJCAI-ECAI-26.zip | yes |
| kdd | OK | ACM Primary Article Template (acmart 2.20) | https://portalparts.acm.org/hippo/latex_templates/acmart-primary.zip | yes |
| sigir | OK | ACM Primary Article Template (acmart 2.20) | https://portalparts.acm.org/hippo/latex_templates/acmart-primary.zip | yes |
| www | OK | ACM Primary Article Template (acmart 2.20) | https://portalparts.acm.org/hippo/latex_templates/acmart-primary.zip | yes |
| ieee | OK | IEEEtran 1.8b (+ bare_conf.tex) | https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip | yes |
| radar | OK | IEEEtran 1.8b in conference mode | https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip | yes |

**Totals: 14 OK · 1 PARTIAL · 0 NOT FOUND.**

---

## Verification log

All archives re-tested after unpacking. `unzip -t` / `tar tzf` reported no errors on any archive, and every file was confirmed to be a real ZIP or gzip stream (the "HTML saved as .zip" failure mode was explicitly checked for and did occur once — see the 403 note below — and was discarded, not shipped).

| Venue | Archive | Size (bytes) | Type | Integrity | Key files confirmed |
|---|---|---|---|---|---|
| neurips | `_original.zip` | 188,273 | Zip | OK | `neurips_2025.sty`, `.tex`, `.pdf` |
| icml | `_original.zip` | 228,368 | Zip | OK | `icml2026.sty`, `icml2026.bst`, `example_paper.tex` |
| iclr | `_original.tar.gz` | 2,673,233 | gzip/tar | OK | `iclr2027_conference.sty/.bst/.tex`, `iclr2026_*`, `iclr2025_*` |
| cvpr | `_original.tar.gz` | 24,496 | gzip/tar | OK | `cvpr.sty`, `main.tex`, `ieeenat_fullname.bst` |
| iccv | `_original.zip` | 33,439 | Zip | OK | `iccv.sty`, `main.tex`, `ieeenat_fullname.bst` |
| eccv | `_original.zip` | 240,506 | Zip | OK | `llncs.cls`, `splncs04.bst`, `eccv2022submission.tex` |
| acl | `_original.tar.gz` | 32,736 | gzip/tar | OK | `acl.sty`, `acl_natbib.bst`, `acl_latex.tex` |
| emnlp | `_original.tar.gz` | 32,736 | gzip/tar | OK | `acl.sty`, `acl_natbib.bst`, `acl_latex.tex` |
| aaai | `_original.zip` | 5,495,535 | Zip | OK | `aaai2027.sty`, `aaai2027.bst`, `CameraReady2027.tex` |
| ijcai | `_original.zip` | 69,002 | Zip | OK | `ijcai26.sty`, `ijcai26.tex`, `named.bst` |
| kdd | `_original.zip` | 15,543,267 | Zip | OK | `acmart.cls`, `ACM-Reference-Format.bst` |
| sigir | `_original.zip` | 15,543,267 | Zip | OK | `acmart.cls`, `ACM-Reference-Format.bst` |
| www | `_original.zip` | 15,543,267 | Zip | OK | `acmart.cls`, `ACM-Reference-Format.bst` |
| ieee | `_original.zip` | 1,727,001 | Zip | OK | `IEEEtran.cls`, `bare_conf.tex`, `bibtex/IEEEtran.bst` |
| radar | `_original.zip` | 1,727,001 | Zip | OK | `IEEEtran.cls`, `bare_conf.tex`, `bibtex/IEEEtran.bst` |

### Traps hit and avoided

1. **HTML masquerading as a ZIP (caught).** `curl` against `https://portalparts.acm.org/hippo/latex_templates/acmart-primary.zip` returned HTTP 403 with `Content-Type: text/html`, saving a 45 KB Cloudflare error page under a `.zip` name. `file` reported "HTML document" and `unzip` reported "End-of-central-directory signature not found". It was detected and re-fetched successfully through the browser session; the HTML file was never staged.
2. **Truncated big downloads (caught twice).** A short `--max-time` silently truncated `media.neurips.cc/.../Styles.zip` at exactly 65,536 B and `aaai.org/authorkit27/` at 105,513 B. Both were re-downloaded with generous timeouts and re-verified.
3. **Wrong entity on a plausible domain (caught).** `eccv.org` is the East Cherry Creek Valley Water & Sanitation District of Colorado, not the European Conference on Computer Vision. Rejected.
4. **Non-official template that looks official (caught).** Overleaf's "Preparation of Papers for IEEE Sponsored Conferences and Symposia" is user-submitted, not IEEE-published. Rejected for the ieee/radar records.
5. **A repo that is not a kit (caught).** `acl-org/emnlp-2025` is EMNLP's Jekyll *website*, not style files. Rejected for emnlp.
6. **Premise in the brief that was wrong (corrected).** `ICLR/iclr20XX` repositories do not exist; ICLR ships every year from the single `ICLR/Master-Template` repo.

### Known environment limitations (not kit defects)

- `www.ieee.org`, `template-selector.ieee.org` and the IEEE DAM asset paths are blocked by AWS WAF from this machine (HTTP 202 + empty body / "Request Rejected").
- `www.acm.org` returns HTTP 403 to plain `curl` (Cloudflare); the ACM template page and the acmart zip had to be retrieved through the browser session.
- `mirrors.ctan.org` returned HTTP 403 for `acmart.zip` while `mirrors.mit.edu/CTAN/...` served the same file (HTTP 200).
- `eccv2024.ecva.net` was unreachable for essentially the whole session (see the eccv Notes).
- `neurips.cc`, `thecvf.com` sub-pages and `aclrollingreview.org/submission` were intermittently unreachable/404; all evidence URLs above were successfully fetched at least once and the findings recorded.

### Repo-level corrections worth knowing downstream

- The CVPR kit repo (`cvpr-org/author-kit`) covers **CVPR/ICCV/3DV**; ICCV *additionally* has its own dedicated kit on CVF's media host. Both are official.
- **ECCV is Springer LNCS-based** (`llncs.cls`), not part of the `cvpr.sty` family.
- **EMNLP = ACL style files**, byte-identical (same sha256).
- **KDD, SIGIR and WWW = the ACM Primary Article Template (`acmart`)**, and the three staged copies are byte-identical; only one real copy is needed.
- **IEEE and RADAR = `IEEEtran` 1.8b**, and those two staged copies are byte-identical as well.

### Disk usage note

Total staging size is ~119 MB, of which ~90 MB is three byte-identical copies of the 15.5 MB ACM `acmart-primary` archive (plus their unpacked trees). If the staging area is later promoted, hardlink or symlink kdd/sigir/www to a single copy, and likewise ieee/radar — the duplication is deliberate here only to satisfy the one-directory-per-venue layout.
