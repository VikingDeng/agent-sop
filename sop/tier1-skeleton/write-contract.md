# SOP-write-contract: 写最小结果契约（按规模选载体）

- **层级**: tier1-skeleton
- **落实纪律**: P1(结果与 non-goals 先于实现)
- **绑定骨架**: development
- **通用性档位**: U1(契约语义通用,载体由项目规模与生命周期决定)
- **版本**: v3

## 触发条件

development 项目或功能在首次语义性实现前，需要把用户目标、现有行为与验收证据收敛为一个可执行结果契约。清晰的小修复同样需要契约，但可以直接从请求、失败复现和现有测试中得到，不要求先写 spec 文件。

## 前置条件

存在待交付的可观察目标；能从用户请求、closest project instructions、现有 spec、行为、测试或 issue 中推出足以开始下一步的范围与验收。只有关键产品语义必须靠猜时，才阻断依赖该语义的实现。

## 依赖 SOP

→ tier0-core/autonomous-supervisor.md（唯一运行时决策源；判定契约粒度、HUMAN 边界与持续状态是否适用）。

## 步骤

1. 优先读取已有项目事实，不重复造文档：确认目标行为、关键 non-goals、允许修改范围、不可接受结果和最便宜的决定性验收证据。
2. 按任务规模选择**一个现有或最轻载体**：
   - 小型、单 session、局部任务：用户请求本身，或活动计划/issue/PR 中的几句话即可；不创建 `spec/`、checkpoint 文件或状态台账。
   - 中型、多模块或可能交接的任务：复用项目已有 `PROJECT.md`、issue、PR、TASK 或计划，写清稳定接口、vertical slice 与完成标准；只有跨 session 信息无法从 Git 与现有载体恢复时，才采用 Supervisor 的轻量 durable state。
   - 新建、长期 product 或具有稳定外部消费者的项目：把长期稳定事实放入项目原生文档；可按需要使用 `spec/REQUIREMENTS.md`、`spec/NON_GOALS.md`、`spec/ARCHITECTURE.md`，但目录和文件名是推荐 recipe，不是通用 gate。
3. 只有新增或改变 public API、协议、数据格式、兼容承诺时，才维护项目的 public contract（例如 `contracts/CONTRACT.md`）；未触及公开表面的内部修改不补造 SemVer/兼容文档。
4. 只有会影响后续实现且无法由代码直观看出的持久决策才记 ADR/decision；临时探索、普通实现选择和可逆局部判断留在活动计划中。
5. 对照 `→ tier0-core/autonomous-supervisor.md` 判断授权：方向已由请求和证据确定时，契约本身就是 autonomous freeze 的记录并立即施工；用户要求同步时可汇报但继续安全工作；只有真实语义分叉、public compatibility、凭据、发布、删除、不可逆状态、法律/隐私或无界成本才进入 HUMAN gate。
6. 区分稳定契约与可变计划：实现顺序、分工、模型、工具和中间方案可随证据改变；不得静默改变目标语义、non-goals 或验收标准。

## 门禁

[AUTO] 仅当无法指出可观察结果、关键边界或任何可信验收方法时，阻断依赖这些信息的实现。

[HUMAN] 仅命中 Supervisor 定义的真实未授权方向时等待决定；继续不依赖该决定的安全工作。

命名文件、目录树、独立 checkpoint 记录、文档数量和 `REQUIREMENTS + NON_GOALS` 的物理存在本身都不是门禁。项目明确选择 strict profile，或长期 public/product 生命周期客观要求正式文档时，才按该项目契约执行。

## 完成判定

- Agent 能指出当前契约的真实载体，并简洁复述结果、non-goals、范围、不可接受结果与验收证据；
- 契约粒度足以安全开始当前 vertical slice，不要求预先解决不阻断当前工作的全部未来细节；
- formal spec、public contract、ADR 与 durable state 只在各自触发条件成立时存在，没有为满足模板而生成空壳。

## 失败处理

若关键产品语义存在多个同样合理方向且只能靠猜，精确提出所需决定并阻断相关部分；普通实现不确定性则通过 prototype、focused oracle 或局部调查收敛。允许随着证据细化计划和内部策略，但不得先实现任意语义再倒写 spec 为其背书，也不得因缺少推荐 artifact 把已明确、可逆的工作判为不可开始。

## 产物

一个与任务规模相称的结果契约，优先存在于用户请求、活动计划、issue、PR 或已有项目文档中；仅在生命周期、交接或 public contract 需要时新增最少的持久文档。
