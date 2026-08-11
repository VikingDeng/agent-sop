# SOP-maintain-patch-series: 按需维护 patch series

- **层级**: tier1-skeleton
- **落实纪律**: P4(需要上游隔离时保持改动可分离、可重放与可追溯)
- **绑定骨架**: competition(code form 要求 patch 或存在持续上游隔离风险)
- **通用性档位**: U1(git/patch 机制通用；上游、应用方式与复现强度参数化)
- **版本**: v2

## 触发条件

满足至少一项时启用：官方提交格式就是 patch；上游必须保持只读；同一改动要在多个 upstream revision 重放；比赛期间会频繁同步上游；或普通分支/commit 无法清楚隔离参赛改动。

仅仅“基于 starter repo 开发”不自动触发。正常 fork/branch 能保留 provenance、比赛要求提交仓库/应用，且没有独立上游重放需求时，直接使用原生 Git 历史通常更简单。

## 前置条件

- 已选定 patch series 而不是普通 branch 的具体理由；
- 知道 upstream 来源与基线 revision、许可/比赛允许的修改方式，以及 `{APPLY_CMD}`/目标树；
- 若要求 exact rebuild，规则或工件风险已说明为什么语义重建/测试不足。

## 依赖 SOP

无(与 package-submission 条件组合)。

## 步骤

1. 冻结 upstream provenance 与基线 revision；可使用现有 remote/ref、submodule、worktree 或 vendored snapshot，不强制复制到 `upstream/{repo}@{commit}/`。
2. 只把需要与上游分离的修改维护为有序 patch。按可独立 apply/review/revert 的逻辑边界拆分；编号与固定命名是 recipe，不是完成门禁。
3. 在干净的目标基线上运行 `{APPLY_CMD}`，验证 patch series 能按序应用；随后运行与提交 claim 匹配的 build/checker/test。只有平台比较原始文件、要求 exact archive/patch，或二进制/打包差异本身会影响 verdict 时才做 byte-identical 比较。
4. upstream 更新时评估是否值得 rebase；若比赛固定旧 revision，就保留已验证基线，不为“保持最新”消耗风险。需要升级时解决冲突并重跑步骤 3 的适用证据。
5. 若 patch series 已比普通 Git 历史更难维护，且比赛不要求 patch，允许显式迁移到 branch/fork；保留旧基线与迁移说明后按同一 acceptance 重验。

## 门禁

- `[BLOCK]` 官方要求 patch/只读上游，却存在未进入 patch series 的目标改动；
- `[BLOCK]` series 不能在声明基线上 apply 或应用后不满足原验收；
- `[SIGNAL]` 普通 starter repo/branch 已能精确追溯时，不建立 vendored tree、PROVENANCE 文档和双重代码源；
- `[REVIEW]` 只有冲突解决、上游许可、patch 顺序或 exact packaging 存在具体风险时复核。

## 完成判定

- 能明确回答 upstream 来源/基线、参赛改动边界和应用方式；
- patch 在声明基线上可重放并通过适用验证；若比赛要求 exact artifact，才证明 exact rebuild；
- 未要求 patch 的项目选择原生 branch 时，不以“没有 patch 目录”判失败。

## 失败处理

patch 不能应用时保留冲突证据，修复或回到已验证 upstream；不得静默丢 patch。发现直接修改只在官方只读/patch 合同下才是违规：把改动转入 series 后重验；若原本合法选择 branch，则继续用 Git 追溯。exact rebuild 不成立时，只有规则确实要求 exactness 才阻断提交；否则报告差异并用匹配 claim 的 build/checker/test 判定。

## 产物

上游 provenance、基线 revision、有序 patch 与一次 apply+verify 结果。具体可复用 remote/ref、Git 历史或现有项目说明；`upstream/`、`patches/NNNN-*`、`PROVENANCE.md` 和 byte-level 重建记录仅在选定 recipe/规则需要时存在。
