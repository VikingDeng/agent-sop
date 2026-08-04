# SOP-release-version: 发布一个版本

- **层级**: tier1-skeleton
- **落实纪律**: P4(版本可追溯:变更、依赖、兼容性有据)
- **绑定骨架**: development
- **通用性档位**: U1(SemVer/CHANGELOG 通用,发布渠道参数化)
- **版本**: v1

## 触发条件

development 骨架项目要对外发布一个版本(库/服务/CLI 的 release)时。

## 前置条件

- 变更已过 `→ tier1-skeleton/drift-check.md` 与验收测试;
- integrated 项目契约测试通过;
- 依赖已锁(`→ tier0-core/lock-env.md`)。

## 依赖 SOP

→ tier0-core/commit-and-pr.md(release 落成可追溯提交/tag)
→ tier0-core/add-dependency.md(新依赖已按流程锁定记录)

## 步骤

1. 判定版本号增量(SemVer):破坏兼容=major、加功能兼容=minor、修 bug=patch。破坏兼容**必须** major bump + 迁移说明。
2. integrated 项目:跑契约测试——任何不兼容改动让契约测试红,逼出 major bump 或回退;不得偷偷破坏兼容发 minor/patch。
3. 废弃(deprecation)按策略:先标废弃 + 保留 N 个版本 + 给迁移路径,再删除;禁止直接删 public API。
4. 更新 `docs/CHANGELOG.md`:本版变更、破坏性变更、迁移说明。
5. 打 tag / 提交(`→ tier0-core/commit-and-pr.md`),产出可发布产物;`{RELEASE_CHANNEL}` 按项目(包索引/镜像仓/内部制品库)。
6. 发布产物与锁文件/CHANGELOG/tag 对应(P4:版本可追溯)。

## 门禁

[AUTO] 契约测试通过(integrated);CHANGELOG 已更新;版本号与变更性质一致。
[REVIEW] 必问:"有没有未标注的破坏性变更被塞进 minor/patch?"

## 完成判定

- 版本号符合 SemVer 且与变更性质一致;
- CHANGELOG + tag + 可发布产物齐备;
- integrated 契约测试通过(二值)。

## 失败处理

遵守 P3:契约测试红 → 中止发布,要么 major bump 要么回退,不得"测试太严先跳过发了";检出破坏兼容却想发 minor/patch → 拦截,不得"用户应该不会用到那个 API 就当兼容";发布产物与 tag/锁文件对不上 → 中止,不静默发一个来源不明的产物。

## 产物

版本 tag + `docs/CHANGELOG.md` 更新 + 可发布产物 + (integrated)契约测试报告。
