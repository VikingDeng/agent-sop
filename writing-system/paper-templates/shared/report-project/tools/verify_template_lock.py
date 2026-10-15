#!/usr/bin/env python3
"""verify_template_lock.py — 校验（或显式重写）本工程的 template.lock。

template.lock 记录 vendor/template/ 快照的模板 id、版本、来源和每个文件的
sha256。`make build` / `make watch` 之前会自动跑**校验**模式；校验只读，
绝不自动改写 lock。升级模板后必须手动重写：

    python3 tools/verify_template_lock.py          # 校验（= make verify）
    python3 tools/verify_template_lock.py --write  # 升级 vendor/ 后显式重写

只依赖 Python 3 标准库，不装任何第三方包。
"""

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = "vendor/template"
LOCK = os.path.join(ROOT, "template.lock")

NOTES = [
    "vendor/template/ 是模板库源码的不可变快照；本工程不依赖 @local/@preview 包，"
    "整个目录拷到别处也能编。",
    "升级模板 = 覆盖 vendor/template/ 下的文件，再手动跑 "
    "python3 tools/verify_template_lock.py --write。",
    "make build / make watch 会先校验本 lock；构建过程不会自动改写它。",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def vendor_files():
    """vendor/template/ 下的全部文件，相对工程根的 POSIX 路径，已排序。"""
    base = os.path.join(ROOT, VENDOR)
    if not os.path.isdir(base):
        sys.exit(f"缺少目录：{VENDOR}/")
    found = []
    for dirpath, _, names in os.walk(base):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
            found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def template_version():
    toml = os.path.join(ROOT, VENDOR, "typst.toml")
    if os.path.isfile(toml):
        with open(toml, encoding="utf-8") as fh:
            m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', fh.read())
        if m:
            return m.group(1)
    return "unknown"


def make_lock(args):
    old = {}
    if os.path.isfile(LOCK):
        with open(LOCK, encoding="utf-8") as fh:
            old = json.load(fh)
    template = args.template or old.get("template")
    source = args.source or old.get("source")
    if not template or not source:
        sys.exit("首次生成 lock 需要：--template <id> --source <来源说明>")
    return {
        "schema": 1,
        "template": template,
        "version": template_version(),
        "source": source,
        "vendored": {
            rel: {"sha256": sha256(os.path.join(ROOT, rel)),
                  "bytes": os.path.getsize(os.path.join(ROOT, rel))}
            for rel in vendor_files()
        },
        "notes": NOTES,
    }


def main():
    ap = argparse.ArgumentParser(description="校验 vendor/template/ 快照的 sha256")
    ap.add_argument("--write", action="store_true",
                    help="显式重写 template.lock（升级模板后手动执行）")
    ap.add_argument("--template", help="仅 --write 用：模板 id")
    ap.add_argument("--source", help="仅 --write 用：模板来源（模板库内路径或 URL）")
    args = ap.parse_args()

    if args.write:
        lock = make_lock(args)
        with open(LOCK, "w", encoding="utf-8") as fh:
            json.dump(lock, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"已重写 template.lock（{lock['template']} {lock['version']}，"
              f"{len(lock['vendored'])} 个文件）；请 review diff 后再提交。")
        return 0

    if not os.path.isfile(LOCK):
        print("template.lock 不存在：跑 python3 tools/verify_template_lock.py --write 生成")
        return 1
    with open(LOCK, encoding="utf-8") as fh:
        lock = json.load(fh)
    recorded = lock.get("vendored") or {}
    problems = []
    for rel, info in sorted(recorded.items()):
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            problems.append(f"缺失: {rel}")
        elif sha256(path) != info.get("sha256"):
            problems.append(f"sha256 不一致: {rel}")
    for rel in vendor_files():
        if rel not in recorded:
            problems.append(f"lock 未记录: {rel}")
    if problems:
        print(f"template.lock 校验失败（{lock.get('template')} {lock.get('version')}）：")
        for p in problems:
            print("  -", p)
        print("vendor/template/ 是模板快照，不要手改；升级请按 README《升级模板》走。")
        return 1
    print(f"template.lock OK：{lock['template']} {lock['version']}，"
          f"{len(recorded)} 个文件 sha256 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
