# SOP-research-execution-grill: 高质量 proposal 执行前拷问

- **层级**: tier1-skeleton
- **落实纪律**: P1(把已批准 proposal 冻结为实现与实验契约) P2(独立审查 claim、oracle 与实验设计) P3(关键歧义和无效设计阻断执行) P4(问题、决议、预算与 scale 决策可追溯)
- **绑定骨架**: research
- **通用性档位**: U2(拷问维度通用,但 proposal 路径、指标、基线、算力、命令与证据由具体研究项目注入)
- **版本**: v1

## 触发条件

- `[信号自触发]` 用户提供或指定一个已经批准、准备实施的科研 proposal,且下一步将写实现、构建实验或消耗算力时;
- `[信号自触发]` pilot 已完成,准备扩大数据、seed、模型、环境或算力规模时;
- `[显式]` 用户要求 grill、red-team、把 proposal 问清楚或检查是否可以进入实现/扩容时。

本 SOP 不生成 idea、不重做 proposal admission、不以措辞偏好否决用户已经批准的研究方向。它只判断 proposal 是否已被翻译成可执行、可证伪、可复现的实现与实验契约。

## 前置条件

- 权威 proposal 位于 `{PROPOSAL_SOURCE}`,有稳定的 `{PROPOSAL_ID}` 与版本或内容 hash;
- 能识别 proposal 的核心 claim、方法机制、目标指标和计划使用的实验资源;
- 项目声明 `{GRILL_ARTIFACT}`、`{GRILL_VALIDATE_CMD}`、`{HUMAN_DECISION_LOG}` 与后续实验入口;
- 拷问者可以读取 proposal 和一手证据,但不得读取实现者对争议点的说服性自评作为独立证据。

## 依赖 SOP

→ tier0-core/build-oracle.md(检查 metric/oracle 是否独立且能发现错误)

→ tier0-core/no-fallback-review.md(检查关键歧义、缺证据和审查失败是否被静默放行)

## 步骤

1. **冻结边界(P1/P4)**:在 `{GRILL_ARTIFACT}` 记录 `{PROPOSAL_ID}`、`{PROPOSAL_SOURCE}`、内容 hash、主控 context ID、核心 claims、明确 non-goals、约束和本次 checkpoint(`pre_implementation` 或 `pre_scale`)。不得在 Grill 中替用户改题或生成替代 idea。
2. **抽取实现歧义(P1/P3)**:逐条寻找会让两个合格实现者得到不同算法、数据流、损失、更新顺序、边界行为或默认值的表述。severity 只能取 P0/critical/high/medium/low。P0/critical/high 只有非空 `proposal:<locator>` 或结构化 HUMAN decision JSON 才能解决;后者必须交叉绑定 proposal/ambiguity/resolution 和另一份带 hash 的人类证据。否则状态必须为 `blocked`,不得用“采用常见做法”静默补全。
3. **建立 claim–experiment 矩阵(P1/P2)**:每个核心 claim 必须绑定 experiment、metric、独立 oracle、success criterion 与 kill criterion。没有可反驳观测的 claim 不得进入正式实验;需要重写 claim 时进入 HUMAN gate,不得由执行者自行改口径。
4. **冻结 baseline fairness(P2)**:逐 baseline 为数据、模型/骨干、调参预算、推理预算、工具权限、停止规则和 judge 各建唯一的 comparability object,其 status 只能取 `matched`、`not_applicable`、`mismatch_mitigated`,并绑定 evidence;mitigated mismatch 还必须给 mitigation。禁止再保留会与 status 冲突的平行自由文本字段。
5. **冻结实验设计(P1/P2)**:记录实验单位与真正独立的 replication unit、assignment/randomization、blocking、nuisance factors、primary estimand、目标效应/MDE、方差依据、sample/seed plan、analysis、multiplicity 和 missing-data。holdout 与 sequential analysis 各只有一个结构化真值源:holdout 禁止 tuning access,sequential analysis 禁止 optional stopping,并将注册 look 数与 scale 契约交叉核对。
6. **攻击 metric 与 oracle(P2)**:列出 shortcut、judge leakage、reward hacking 和数据污染,为每项指定 detection/negative control。oracle independence 只有一个结构化对象,必须同时声明 independent=true、shared implementation path=false 并绑定证据。调用 `→ tier0-core/build-oracle.md`;被测实现不得复用同一路径自证。
7. **定义 pilot→scale 契约(P1/P3/P4)**:用带唯一 ID、operator 与 threshold 的结构化 condition 列表分别冻结 pilot pass、scale 和 kill;声明所有 scale conditions 必须满足、任一 kill condition 必须停止。interim schedule 的条目数必须等于注册 look 上限并与 design 一致。`pre_scale` evidence 必须是绑定 proposal 与 pilot-plan hash 的严格 JSON,逐 condition ID 记录 observed value,并用原始 JSON 结果文件、实际 SHA-256 与 JSON Pointer 绑定其数据来源,交给 validator 重新取值和重算;任意文本、agent 自报数字、幸运单点或事后切片不得解锁 scale。
8. **冻结复现与预算(P3/P4)**:记录环境锁、代码引用策略、数据版本、manifest、GPU/token/wall-clock 上限和触顶动作。缺少任一适用上限时保持 `blocked`;不得以“先跑再补”为由放行。
9. **独立内部审查(P2)**:发起审查前先在 Grill core 内冻结完整 `review_plan`,逐项写唯一 reviewer ID、type、隔离 context 与 allowlisted GPT model。再由计划中的只读 GPT/Codex reviewer 只读 proposal、一手证据和 `{GRILL_ARTIFACT}` 后给出 pass/blocked 与结构化 findings。输入 packet 和 review JSON 必须是不同的非空文件,分别带 SHA-256并交叉绑定 proposal/checkpoint/Grill core hash。每项 finding 记录 severity 与 open/resolved;reviewer context 必须不同于主控 context,类型必须是 `internal_blind_gpt`,model 只能取契约 allowlist。ready 时计划内审查必须全部出现,且均不得 blocked 或保留 open P0/critical/high finding;一份 pass 不得覆盖或删除另一份反对意见。修改 review plan 会使旧 review hash 失效;人类审查可追加,不能替代。
10. **机器判门(P3/P4)**:运行 `{GRILL_VALIDATE_CMD} {GRILL_ARTIFACT} --required-checkpoint {REQUIRED_CHECKPOINT}`。实现/pilot 要求 `pre_implementation`,物质性扩容要求 `pre_scale`;退出码 `0` 才允许对应动作。结构错误、blocked 状态、P0 未清零、审查缺失或 validator 崩溃均阻断。修改 proposal、claim、metric、数据划分、baseline 预算或 scale 判据后,必须更新 hash 并重跑本 SOP。

字段契约与示例见 [references/research-execution-grill-artifact.md](references/research-execution-grill-artifact.md)。仓库提供的参考 validator 为 `scripts/validate_research_execution_grill.py`。

## 门禁

- `[AUTO][阻断型]` `{PROPOSAL_ID}`、source/hash、checkpoint、claims 与 non-goals 已冻结;
- `[AUTO][阻断型]` 每个 claim 都有 experiment/metric/oracle/success/kill 映射;
- `[REVIEW][阻断型]` baseline fairness、实验单位、replication、holdout、interim look、metric shortcut 和 negative control 均有显式结论;
- `[REVIEW][阻断型]` 预冻结 review plan 已全部兑现,至少一份隔离上下文的内部盲审为 pass;GPT/Codex 审查不得标为 external review,且全部计划内审查均无 blocked verdict 或 open blocking finding;
- `[RUNTIME][阻断型]` `{GRILL_VALIDATE_CMD}` 退出码为 `0`;缺 validator 或 validator 崩溃不是通过;
- `[HUMAN]` 只有 P0 歧义需要改变 claim、方法语义、成功标准、资源承诺或 proposal 边界时才等待人裁决。

## 完成判定

以下条件全部为 true 才完成:

- `{GRILL_ARTIFACT}` 与当前 `{PROPOSAL_SOURCE}` hash 一致;
- 状态为 `implementation_ready` 或 pre-scale 时为 `scale_ready`;
- unresolved P0/critical/high ambiguity 和 human gate 均为零;
- claim–experiment、baseline fairness、实验设计、oracle attack、pilot→scale、复现和预算字段完整;pre-scale 时 validator 已从逐 condition observed values 重算出 all-pass/no-kill;
- `review_plan` 与 Grill core hash 绑定且全部兑现;至少一份交叉哈希一致的 `internal_blind_gpt` 结构化审查为 pass,且其余计划内审查没有 blocked verdict 或 open blocking finding;人类审查是追加证据,不能替代;
- `{GRILL_VALIDATE_CMD} {GRILL_ARTIFACT} --required-checkpoint {REQUIRED_CHECKPOINT}` 实际退出码为 `0`。

## 失败处理

遵守 P3:关键歧义未解决、claim 无法证伪、baseline 无法公平比较、实验单位不清、样本/seed 无依据、holdout 可被调参访问、metric 可被明显钻空子、预算无上限、独立审查不可用或 validator 非零时,状态保持 `blocked` 并列出最小待决问题;不得自动改 proposal、降低 success criterion、增加事后切片、把重复测量当独立样本、把同一 GPT 的第二次回答伪装成 external review,或绕过 Grill 直接进入实现/scale。若问题需要改变用户批准的 proposal 语义,写入 `{HUMAN_DECISION_LOG}` 后停在 HUMAN gate。

## 产物

- `{GRILL_ARTIFACT}`:proposal hash、checkpoint、歧义与决议、claim–experiment、baseline fairness、实验设计、oracle attack、pilot→scale、复现、预算和 review 记录;
- `{HUMAN_DECISION_LOG}`:仅包含需要改变 proposal 语义或资源承诺的待决项及最终裁决;
- `{GRILL_VALIDATE_CMD}` 的命令、退出码与输出摘要;
- `implementation_ready`、`scale_ready` 或 `blocked` 三者之一的可复核结论。
