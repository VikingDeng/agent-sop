# PATCHES — `clear-iclr`

## Why this directory exists

The published package `@preview/clear-iclr:0.7.0` **does not compile on Typst
0.15.1**. The break is in the template's own demo document, not in its style
library, so the fix is a rename in the demo text.

| | |
|---|---|
| Upstream | <https://github.com/daskol/typst-templates> |
| Upstream path | `iclr/` |
| Upstream version | 0.7.0 (tag) |
| Vendored from | repository HEAD, commit `3394b81` ("Allow font configuration for `neurips` template (#71)", 2026-05-01) |
| Vendored on | 2026-09-17 |
| License | MIT — © 2023 Daniel Bershatsky (see `LICENSE`, retained unmodified) |
| Local package | `@local/clear-iclr:0.7.1` (version bumped to mark the patch) |

## The patch

**File:** `main.typ`
**Lines:** 285 and 289

```diff
-  $display((diff y) / (diff x))$, [Partial derivative of $y$ with respect to $x$],
+  $display((dif y) / (dif x))$, [Partial derivative of $y$ with respect to $x$],
```

and the same substitution on the Jacobian line.

### Why the original fails

Typst **renamed the partial-derivative math shorthand from `diff` to `dif`**.
In Typst 0.15.1:

```
$ dif x $    ->  ∂x     ✅
$ diff x $   ->  error: unknown variable: diff
$ partial x$ ->  ∂x     ✅   (also works)
```

Verified directly:

```
$ printf '#$ dif x $\n'  > t.typ; typst compile t.typ   # OK
$ printf '#$ diff x $\n' > t.typ; typst compile t.typ   # unknown variable: diff
```

⚠ Because Typst treats a bare unknown identifier in math mode as a variable
reference, this fails rather than silently rendering the letters "diff".

### Scope of the change

Only the demo document was affected — the style library `iclr.typ` /
`iclr2025.typ` / `iclr2026.typ` contains no `diff` usage. A search of the whole
vendored tree confirms `main.typ` was the only file:

```
$ grep -rn '\bdiff\b' --include=*.typ .
./main.typ:285:  $display((diff y) / (diff x))$, ...
./main.typ:289:  $display((diff f) / (diff bold(x)))$, ...
```

**This means the published package is usable as-is if you never compile its
demo** — `#import "@preview/clear-iclr:0.7.0": iclr2026` still works, because
the broken lines are demo prose, not library code. The local package exists so
that the demo also compiles and so that the whole library builds uniformly.

### Verification

```
$ cd typst/iclr && typst compile main.typ out.pdf
✔ out.pdf, 153439 bytes
```

## Reporting this upstream

Not yet reported. Reproduction:

```
typst init @preview/clear-iclr:0.7.0 iclr-test
cd iclr-test && typst compile main.typ
# error: unknown variable: diff
#   ┌─ main.typ:285:12
```

## How to re-sync with upstream

```bash
git clone --depth 1 https://github.com/daskol/typst-templates /tmp/daskol
cp -r /tmp/daskol/iclr/. typst/iclr/
sed -i 's/\bdiff\b/dif/g' typst/iclr/main.typ
scripts/install-local-typst-packages.sh
```
