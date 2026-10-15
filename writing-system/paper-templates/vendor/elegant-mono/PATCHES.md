# PATCHES — `elegant-mono`

A locally patched copy of **`@preview/elegant-paper:0.1.0`** with every colour
removed, so the output is pure black and white and prints identically on a
mono laser printer.

| | |
|---|---|
| Upstream | <https://github.com/ctypst/elegant-paper-typst> |
| Upstream package | `@preview/elegant-paper:0.1.0` |
| Author | Xyber Nova `<xyber-nova@outlook.com>` |
| License | **LGPL-3.0** — see `LICENSE.md`, retained unmodified |
| Vendored from | the local Typst package cache, 2026-09-18 |
| Local package | `@local/elegant-mono:0.1.0` |

## The patch

**File:** `lib.typ`
**Occurrences:** 2

```diff
       show ref: it => {
-        set text(fill: color.rgb(128, 0, 0))
+        set text(fill: color.rgb(0, 0, 0))
         it
       }
...
         show outline.entry: it => {
-          set text(fill: color.rgb(128, 0, 0))
+          set text(fill: color.rgb(0, 0, 0))
           it
         }
```

### Why a patch and not a show-rule override

Both colours are set inside `elegant-paper`'s own scope block, and the
`outline()` element is *constructed by the template*, not by the caller's
document. A `show outline.entry: set text(fill: black)` written in the user's
file therefore never reaches it — verified empirically: the rendered TOC still
sampled `#8E1D1D` (an anti-aliased `rgb(128,0,0)`) after adding that override.

The affected elements are:

1. **cross-references** (`show ref`) — e.g. a rendered “图 1”
2. **table-of-contents entries** (`show outline.entry`)

## Licence note

`elegant-paper` is **LGPL-3.0**, not MIT. This patched copy therefore
- keeps `LICENSE.md` verbatim,
- declares `license = "LGPL-3.0"` in its own `typst.toml`,
- is registered under a **different package name** (`elegant-mono`) so it can
  never be mistaken for upstream,
- and documents its changes here, as the licence requires.

If you redistribute anything built on this, LGPL obligations attach to the
template. Using it locally to typeset your own document does not.

## Re-sync with upstream

```bash
# refresh the vendored source, then re-apply the colour change
cp ~/.cache/typst/packages/preview/elegant-paper/<ver>/lib.typ vendor/elegant-mono/lib.typ
sed -i 's/color\.rgb(128, 0, 0)/color.rgb(0, 0, 0)/g' vendor/elegant-mono/lib.typ
scripts/install-local-typst-packages.sh
```
