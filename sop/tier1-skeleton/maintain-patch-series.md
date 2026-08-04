# SOP-maintain-patch-series: 维护 patch series(上游隔离)

- **层级**: tier1-skeleton
- **落实纪律**: P4(改动可分离、可重放、可追溯到上游 commit)
- **绑定骨架**: competition(code 形态 patch/clone)
- **通用性档位**: U1(git patch 机制通用,上游 repo 参数化)
- **版本**: v1

## 触发条件

competition 骨架中 code 形态为 patch 或 clone,需要在别人仓库/starter repo 上做改动时。

## 前置条件

- 上游 repo 已 vendored 并锁 commit:`upstream/{repo}@{commit}/`(只读基线);
- `PROVENANCE.md` 记了上游 URL / commit / license / apply 步骤。

## 依赖 SOP

无(与 package-submission 配合:提交时 apply patches 重建产物)。

## 步骤

1. 铁律确认:上游 vendored 树**只读**,你的改动只以 `patches/NNNN-{desc}.patch` 存在,**绝不直接 commit 到 vendored 树**。
2. 每个逻辑改动一个 patch,命名含序号+描述(`0001-double-buffer.patch`),便于按序 apply 与 rebase。
3. clone 形态:自己的代码放独立 `src/{pkg}/`,通过 `adapters/` 对接上游,禁止散落 monkey-patch;必须改上游文件时仍走 patches/。
4. 可重建验证:`vendored 快照` apply `patches/*` 应字节级得到最终产物;做不到即台账失效。
5. 上游升级时:换 `{commit}`,按序 rebase patch series,解决冲突后重验步骤 4。

## 门禁

[SCAN] vendored 树无本地直接 commit(只读校验);产物可从 `{commit}+patches` 重建。
[REVIEW] 必问:"有没有绕过 patches 直接改了 vendored 树?patch 能干净 apply 吗?"

## 完成判定

- 改动全部以 patch series 存在,vendored 树未被直接修改;
- apply patches 能字节级重建产物(二值)。

## 失败处理

遵守 P3:若发现有改动直接落进 vendored 树 → 判台账失效,回退并转成 patch,不得"已经改了就将就";patch 无法干净 apply/重建对不上 → 报错中止,不得"手动补一下差异凑上"(那会破坏可重放性);上游升级 rebase 冲突无法解决 → 如实报告,不静默丢弃某个 patch。

## 产物

`upstream/{repo}@{commit}/`(只读)+ `patches/NNNN-*.patch`(有序)+ `PROVENANCE.md`;可重建的最终产物。
