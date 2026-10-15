# PATCHES — `lucky-icml`

## Why this directory exists

The published package `@preview/lucky-icml:0.7.0` **does not compile on Typst
0.15.1**. Rather than leave the ICML slot empty, the upstream source was
vendored from the author's repository and given a one-line fix.

| | |
|---|---|
| Upstream | <https://github.com/daskol/typst-templates> |
| Upstream path | `icml/` |
| Upstream version | 0.7.0 (tag) |
| Vendored from | repository HEAD, commit `3394b81` ("Allow font configuration for `neurips` template (#71)", 2026-05-01) |
| Vendored on | 2026-09-17 |
| License | MIT — © 2023 Daniel Bershatsky (see `LICENSE`, retained unmodified) |
| Local package | `@local/lucky-icml:0.7.1` (version bumped to mark the patch) |

## The patch

**File:** `icml2024.typ`
**Line:** 165 (in the vendored copy)

```diff
     assert(type(affl) == array,
-           message: "wrong affilation type: " + type(affl))
+           message: "wrong affilation type: " + repr(type(affl)))
```

### Why the original fails

Typst evaluates **all** arguments of a function call eagerly, including a named
argument that a conditional construct would only need on one branch. In

```typst
assert(condition, message: "…" + type(affl))
```

the `message` expression is constructed on **every** call to `assert`, whether
or not `condition` holds. `"string" + type` is not a valid addition, so the
call raises `cannot add string and type` unconditionally — the assert never
even gets to report whether the affiliation was malformed.

In other words the bug is not in the affiliation-handling logic (which is
fine); it is an error *message* that can never be built. Wrapping in `repr`
makes the concatenation legal while producing the same diagnostic text.

### Verification

```
$ cd typst/icml && typst compile main.typ out.pdf
warning: unknown font family: times new roman      <- benign, see below
✔ out.pdf, 187903 bytes
```

The `times new roman` warning is cosmetic. The template's font stack is
`("Times New Roman", "Nimbus Roman", "TeX Gyre Termes")`; Typst warns about
each name it cannot find and then uses the first one it can. The produced PDF
embeds `NimbusRoman-Regular/Bold/Italic/BoldItalic` and `NewCMMath-Book`, i.e.
a Times-metric serif and the correct math font.

## Reporting this upstream

Not yet reported. If you file an issue, the reproduction is:

```
typst init @preview/lucky-icml:0.7.0 icml-test
cd icml-test && typst compile main.typ
# error: cannot add string and type
#   ┌─ @preview/lucky-icml:0.7.0/icml2024.typ:165:20
```

## How to re-sync with upstream

```bash
git clone --depth 1 https://github.com/daskol/typst-templates /tmp/daskol
cp -r /tmp/daskol/icml/. typst/icml/
# re-apply the one-line fix above, then:
scripts/install-local-typst-packages.sh
```

Check first whether upstream has fixed it — if the package on Typst Universe is
re-published at a version that compiles on your Typst, prefer `@preview` and
delete the local package.
