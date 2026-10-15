#!/usr/bin/env python3
"""compare_pdf.py — 逐页比较两个 PDF 的文本与像素。

只依赖标准库 + poppler-utils（pdfinfo / pdftotext / pdftoppm），不联网、不装包。
不做任何图像解码：pdftoppm 把每页输出成 PPM，直接比文件字节，字节相同即像素零差异。

用法:  python3 tools/compare_pdf.py A.pdf B.pdf [--outdir DIR] [--dpi 150]
产物:  DIR/compare.json、DIR/page-NN-a.png / -b.png（最多 3 页代表截图）
退出码: 0 = 页数、逐页文本、逐页 PPM 字节全同；1 = 有差异或执行失败。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout


def page_count(pdf):
    for line in run(["pdfinfo", pdf]).splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1])
    raise RuntimeError(f"pdfinfo 未报告页数: {pdf}")


def page_text(pdf, page):
    """该页 pdftotext -layout 文本。"""
    return run(["pdftotext", "-layout", "-f", str(page), "-l", str(page), pdf, "-"])


def render(pdf, page, stem, dpi, png=False):
    """整页渲染；-singlefile 得到 <stem>.ppm（png=True 时输出 <stem>.png）。"""
    cmd = ["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page)]
    if png:
        cmd.append("-png")
    run(cmd + ["-singlefile", pdf, stem])
    return stem + (".png" if png else ".ppm")


def same_bytes(pa, pb):
    with open(pa, "rb") as fa, open(pb, "rb") as fb:
        return fa.read() == fb.read()


def main():
    ap = argparse.ArgumentParser(description="逐页比较两个 PDF（文本 + PPM 字节）")
    ap.add_argument("pdf_a", help="旧 PDF（基线）")
    ap.add_argument("pdf_b", help="新 PDF")
    ap.add_argument("--outdir", default=None, help="写 compare.json 与代表截图")
    ap.add_argument("--dpi", type=int, default=150, help="渲染 dpi（默认 150）")
    args = ap.parse_args()

    a, b = args.pdf_a, args.pdf_b
    if os.path.abspath(a) == os.path.abspath(b) or (
            os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)):
        ap.error("两个参数指向同一个文件，无法比较")
    for tool in ("pdfinfo", "pdftotext", "pdftoppm"):
        if shutil.which(tool) is None:
            sys.exit(f"缺少 {tool}（需要 poppler-utils）")
    try:
        na, nb = page_count(a), page_count(b)
    except RuntimeError as exc:
        sys.exit(str(exc))

    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
    pages = max(na, nb)
    samples = sorted(dict.fromkeys([1, (pages + 1) // 2, pages]))[:3] if pages else []
    work = tempfile.mkdtemp(prefix="compare-pdf-")
    per_page, text_diff, pixel_diff = [], [], []
    try:
        for page in range(1, pages + 1):
            rec = {"page": page}
            if page > na or page > nb:
                rec["status"] = "missing-in-one-pdf"
                text_diff.append(page)
                pixel_diff.append(page)
            else:
                ta, tb = page_text(a, page), page_text(b, page)
                pa = render(a, page, os.path.join(work, f"a-{page:02d}"), args.dpi)
                pb = render(b, page, os.path.join(work, f"b-{page:02d}"), args.dpi)
                rec["text_equal"] = ta == tb
                rec["pixels_equal"] = same_bytes(pa, pb)
                if not rec["text_equal"]:
                    text_diff.append(page)
                if not rec["pixels_equal"]:
                    pixel_diff.append(page)
                if args.outdir and page in samples:
                    for tag, src in (("a", a), ("b", b)):
                        render(src, page, os.path.join(
                            args.outdir, f"page-{page:02d}-{tag}"), args.dpi, png=True)
                os.remove(pa)
                os.remove(pb)
            per_page.append(rec)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    same = na == nb and not text_diff and not pixel_diff
    summary = {
        "pdf_a": os.path.abspath(a), "pdf_b": os.path.abspath(b), "dpi": args.dpi,
        "pages_a": na, "pages_b": nb, "pages_equal": na == nb,
        "text_identical": na == nb and not text_diff,
        "pixels_identical": na == nb and not pixel_diff,
        "text_diff_pages": text_diff, "pixel_diff_pages": pixel_diff,
        "same": same, "samples": samples if args.outdir else [], "per_page": per_page,
    }
    if args.outdir:
        with open(os.path.join(args.outdir, "compare.json"), "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
    text_ok = summary["text_identical"]
    pixel_ok = summary["pixels_identical"]
    print(f"A(基线) = {summary['pdf_a']}\nB(新稿) = {summary['pdf_b']}")
    print(f"页数: A={na} B={nb} {'一致' if na == nb else '不一致'}")
    print(f"pdftotext -layout 文本: {'完全一致' if text_ok else '有差异 -> ' + str(text_diff)}")
    print(f"pdftoppm PPM 字节: {'完全一致' if pixel_ok else '有差异 -> ' + str(pixel_diff)}"
          f" (dpi={args.dpi})")
    if args.outdir:
        print(f"摘要: {os.path.join(args.outdir, 'compare.json')} / 代表截图页: {samples}")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
