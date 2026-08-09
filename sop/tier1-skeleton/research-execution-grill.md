# SOP-research-execution-grill: 高质量 proposal 执行前拷问

- **层级**: tier1-skeleton
- **落实纪律**: P1(冻结执行契约) P2(独立签名审查) P3(状态机硬阻断) P4(事件与证据可追溯)
- **绑定骨架**: research
- **通用性档位**: U2
- **版本**: v4 (`research-execution-grill-v3` / artifact schema v3)

## 触发条件

- 已批准 proposal 即将进入证据获取、人工 oracle、Phase 0 或物质性扩容;
- 用户显式要求 grill、red-team 或检查 exact action authorization。

本 SOP 不生成替代 idea、不重做 proposal admission,只把已批准方向冻结为可执行、可证伪、可复现的契约。

## 前置条件

- proposal 有稳定 ID、source 与内容 hash;
- 项目声明 Grill artifact、外部 pinned trust policy、signed event ledger 与实验入口;
- reviewer、human oracle、runtime attestor 与 lineage authority 的边界明确。

## 依赖 SOP

→ tier0-core/build-oracle.md

→ tier0-core/no-fallback-review.md

## 步骤

1. **选择唯一授权协议(P1/P3)**:新授权只能使用 `schema_version: 3` 与
   `research-execution-grill-v3`。v1/v2 只能分别用 `--audit-v1`/`--audit-v2`
   审计并退出 `4`,绝不进入 v3 authorization。
2. **冻结 checkpoint 与动作顺序(P1/P4)**:authoritative pure state machine 中一个 signed `checkpoint_opened`
   覆盖 exact order `static_acquisition -> human_oracle -> phase0_launch -> scale_launch`。
   finalized actions 必须形成 exact prefix;禁止 skip、reopen、duplicate open、out-of-order、
   terminal 后追加和 project-local reset。
3. **分离 acquisition 与实验(P1/P3)**:`bootstrap/evidence_acquisition` 与
   `experiment_authorization` 分离。bootstrap MUST NOT 运行 subpilot/pilot/experiment、
   计算 scientific metrics、inspect outcomes for adaptation 或输出 scientific claims。
   检查 required artifact IDs、provided artifact IDs、disjointness 与 dependency cycle。
4. **冻结 action evidence(P1/P4)**:`action_opened` 绑定 action-specific immutable
   core、完整 evidence manifest、frozen review-plan hash 和当前 ledger tail。manifest
   逐 consumed artifact 记录 ID、kind/class、producer、source/semantic hash、完整
   attestation payload、signature identity 与 consumed hashes。任何 identity 漂移都改变 manifest。
5. **保持四个能力边界(P3)**:Code Readiness 是 synthetic/nonauthorizing evidence,
   只支持 Static Acquisition,且不需要 future labels;其 content-bound code-test contract
   与完整 signed code review 缺一不可。Human Oracle 至少消费 verified source registry 与
   blinded audit bundle。Phase 0 需要 exact registry/bundle、sealed human labels/derivation、clean
   reproduction、finite positive budget 与 signed runtime capability。Scale 还必须包含 exact
   designated bundle、Phase 0 raw/result identities、condition 重算、kill gates 与 finite scale budget。
6. **独立签名审查(P2/P4)**:完整 planned reviewer set 的每份 review 必须绑定 action、
   opened-event hash、core、manifest、plan、reviewer identity/role/context/model、phase、verdict、
   normalized findings 与 source/semantic/attestation hashes。冻结计划中的 `reviewer_id`、
   `signer_identity` 与 `reviewer_context_id` 分别非空且各自唯一,三者形成一对一 slot;
   signer/context 不得跨 reviewer 共用或在 initial/re-review 间交换。`review_cycle_hash` 对排序后的
   planned set 与完整 signed reviews 做 canonical projection,排除 path/signature transport。
7. **执行单次修正收敛(P3)**:initial pass 可直接 finalization。initial blocked 只允许一次
   `correction_applied`,绑定 opened event、完整 blocked `initial_review_cycle_hash` 与
   before/after core+manifest,随后只允许一次完整
   re-review。re-review pass → `authorized`;blocked → terminal
   `architecture_reset_required`。禁止 second correction、A→B/A→C branching 或 reopen。
8. **两阶段外部授权(P3/P4)**:validator 用 `--prepare-event` 或
   `--prepare-authorization ACTION` 生成 canonical candidate,以 exit `5`
   `PREPARED_NOT_AUTHORIZED` 返回。candidate path 必须 exclusive/no-overwrite。
   validator 不签名、不 append ledger;外部 `lineage_authority` 在 lock 下 atomic append。
   prepare 与 required authorization 都必须提供 observed tail 的 external
   `--lineage-tail-sha256`;空 ledger 只接受显式 `EMPTY` sentinel。
9. **验证 canonical event(P3/P4)**:event body 冻结 seq、previous hash、event type、
   checkpoint/proposal/lineage/protocol、requested action、signer principal/role、event bindings、
   expected tail 与 outcome。`event_hash` 是 body canonical SHA-256。OpenSSH detached signature
   覆盖 canonical `{"body": body, "event_hash": event_hash}`,使用 v3 lineage namespace;
   signature path 在 hash body 外。canonical hash 不是 signature 或 permission。
10. **重读后授权(P3)**:运行
    `{GRILL_VALIDATE_CMD} {GRILL_ARTIFACT} --required-authorization {ACTION} --trust-policy
    {TRUST_POLICY} --trust-policy-sha256 {EXTERNAL_PIN} --lineage-ledger {LEDGER}
    --lineage-tail-sha256 {EXTERNAL_LEDGER_TAIL}`。
    只有 exact action 的 signed final event、core、manifest、review cycle 与完整 evidence
    全部重验后 exit `0` 才是 permission。
11. **分离错误通道(P3)**:malformed/invalid/stale/untrusted/contract error → exit `1`;
    operational unavailable 或 action 尚未授权 → exit `3`;legacy audit → `4`;candidate prepared → `5`。
    correctly signed `runtime_available=false` 是 `operational_blocked`;任何 evidence class 的
    malformed/unsigned/hash-mismatched/forged/wrong-role envelope 都是 contract error。
    不得把 operational failure 写成 scientific no-go。
12. **保留 approved-proposal 语义(P1)**:Grill 可阻断歧义、无效设计、不公平 baseline、
    弱 oracle、缺预算或证据漂移,但不得生成 replacement idea 或擅自降低 success criterion。

字段与 event 示例见
[references/research-execution-grill-artifact.md](references/research-execution-grill-artifact.md)。

## 门禁

- `[STATE][阻断型]` pure state machine 接受 signed ledger 后得到 valid exact prefix;
- `[TRUST][阻断型]` trust policy external pin、artifact/review/event signatures 与 roles 全部通过;
- `[REVIEW][阻断型]` final event 引用 retained complete signed review cycle;
- `[EVIDENCE][阻断型]` action core 与完整 manifest 匹配当前 source/semantic/attestation identities;
- `[RUNTIME][阻断型]` exact `--required-authorization ACTION` 实际 exit `0`;
- `[HUMAN]` 只有改变 proposal 语义、claim 或资源承诺才进入人类决策。

## 完成判定

- payload proposal/source hash、schema/protocol 与 checkpoint ID 一致;
- external authority 已签名并 atomic append action final event;
- validator 重读 ledger、trust、evidence 与 review cycle 后对 exact action exit `0`;
- payload status/authorization 仅作 derived informational output,不参与决策。

## 失败处理

任何非零 required-authorization 结果都不得执行相应动作。exit `5` 只是待签 candidate。
若 tail 在 prepare 后变化,丢弃 stale candidate 并从新 tail 重新 prepare。terminal
`architecture_reset_required` 撤销本 checkpoint 内所有先前 action authorization;此后不得
append、复制 vN 或本地 re-contract 伪装 reset。

## 产物

- schema v3 Grill artifact 与 action evidence manifest;
- external pinned trust policy;
- append-only signed v3 event ledger;
- canonical candidate、external signature、review-cycle hash 与 validator exact exit evidence。
