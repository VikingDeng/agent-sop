# 维护本仓库

- 规则只写一处：KERNEL 写通用规则，playbook 只写某类任务特有的部分，其他地方用链接引用，不复制。
- 新增或修改规则要有来源：一条复盘（`retro/`）中记录的真实失败，而且它可能复发、换一个任务也适用。规则只约束结果、证据和边界，不规定做法。
- 有篇幅上限：`python3 scripts/check_docs.py` 会检查链接和字数。超出上限时，先删掉其他内容，再加新内容。
- 新增 playbook 的前提是同类任务至少已经做过一次，并写过复盘。
- `writing-system/` 是 `/home/viking/dev/docs/_shared` 的只读快照，被本机写作 skill 通过 vendor 快照引用。不要在这里改它：改动回到维护源，按 [writing-system/FREEZE.md](writing-system/FREEZE.md) 登记后，再整体同步快照。
- 不 force-push，不跳过 hook，不直接推 main；在分支上改，开 PR。
