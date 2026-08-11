# SOP-ops-remote-compute: 远程算力使用规程（SSH 作业）

- **层级**: tier2-activity
- **落实纪律**: P1(冻结远程 work packet)/ P3(失败即停、科研 run 无自动 fallback)/ P4(主机到产物可追溯)
- **绑定骨架**: 无（research/development 项目需要远程资源时按需调用）
- **通用性档位**: U1（主机、工作区、资源预算和命令由项目 profile 注入）
- **版本**: v2

## 目标

在已授权远程资源内自主、克制、可恢复地执行计算任务；让每个 evidence-bearing run 能回到主机、GPU、代码、环境、命令、进程、成本和原始产物，同时不把主机故障或能力缺失变成静默的本地/CPU/backend fallback。

## 触发条件

- 用户或项目契约要求在远程主机运行实验、训练、评测、数据处理或长时任务；
- 本地资源不足，而切换到远程资源仍位于已授权 outcome contract；
- 需要规划或复核远程资源、工作区、数据/模型下载、监控和产物回收。

## 前置条件

- 项目声明远程 profile：`{HOST}`、`{REMOTE_WORKSPACE}`、允许的 GPU/CPU/内存/磁盘/时长或费用上限，以及 `{ENV_CMD}`/`{LOCK_FILE}`；
- `{HOST}` 可由 SSH config 与受治理的服务器清单解析；不得把密码、私钥、token 或敏感连接材料写入仓库和日志；
- 待执行任务已有 evidence class、明确命令/入口、预期产物、kill criteria 和失败语义；
- 科研正式 run 已冻结 claim、method、数据/split、分析方法和预算，或明确仅为 `paper_eligible=false` 的 smoke/code-readiness。

个人工作区可在 `codex/AGENTS.workspace.md` 注入默认主机；通用 SOP 不猜 IP、用户、卡号或路径。

## 依赖 SOP

→ tier0-core/no-fallback-review.md（失败与替代路径语义）。

→ tier0-core/lock-env.md（远程环境与依赖身份）。

→ tier0-core/commit-and-pr.md（代码与必要操作记录的 Git 留痕）。

## 步骤

1. **冻结 remote work packet 与 checkpoint**：记录 `{HOST}`、`{REMOTE_WORKSPACE}`、repo/ref、evidence class、资源上限、命令/入口、输出位置、kill criteria、预期时长和 paper eligibility。若这些均已由项目协议授权，记录 `AUTONOMOUS_CHECKPOINT` 后继续；不要再次询问主机/卡/路径。只有新主机或凭据、共享资源冲突、未授权工作区、material/unbounded cost、生产/公开动作或不可逆操作进入 `MANDATORY_HUMAN_CHECKPOINT`。
2. **非交互身份与资源预检**：从服务器清单和 `ssh -G {HOST}` 解析目标，以 `ssh -o BatchMode=yes -o ConnectTimeout=10 {HOST} true` 验证认证；失败即停，禁止 `sshpass`/expect/密码落盘。只读检查 OS/架构、`who`、GPU/显存、CPU/内存、磁盘、负载、自己的现有任务，以及远程 repo root、commit/dirty state 和环境身份。主机、路径或资源与 packet 不符时不启动 run。
3. **在授权目录准备代码、环境与输入**：所有写入限定在 `{REMOTE_WORKSPACE}` 和约定数据根。代码用 Git 同步；权重、数据和大 artifact 在服务器按项目 registry/version/checksum 下载或读取，不经本地大文件中转。用 `{ENV_CMD}` 与 `{LOCK_FILE}` 构建/验证项目环境；未经授权不 `sudo`、不改系统目录、不覆盖共享环境，也不把 secret 写进 shell history 或 manifest。
4. **分离 code readiness 与 evidence run**：需要时先以独立 run ID 运行最小 smoke，验证 wiring、schema、异常路径、资源估计和输出格式；它必须 `paper_eligible=false`，使用独立输出目录，不能调参、触发 scientific GO 或被后续正式表消费。smoke 通过后，正式实验由单独命令和新 run ID 启动；不得在同一进程中自动从 smoke/fallback 路径升级为正式证据。
5. **受限启动且 fail fast**：显式设置所用设备和并发，例如 `CUDA_VISIBLE_DEVICES={GPU_SET}`，不抢占清单外资源。长任务用项目允许的 `tmux`/`nohup`/scheduler，立即记录 PID/job/session、完整命令、日志、host/GPU、repo SHA、环境、开始时间和预算。科研 run 的 model/backend/device/data/metric/method component 不满足时非零退出；禁止自动切本地、CPU、其他 backend/model/host 后继续产出证据。
6. **低干扰监控**：日志与结构化 status 写在项目工作区；使用与任务时长相称的长间隔或 scheduler 状态，不做高频 polling。wait/SSH timeout 只表示状态未知或仍运行，不代表成功/失败。触及 kill criteria 或预算时只终止本 packet 记录的进程并保留现有产物；crash、OOM、preemption 和 timeout 使用不同状态，不填成科学负结果或 0。
7. **收集并验证产物**：保留 raw results、配置、日志、manifest/checker 输出、实际 compute 和失败信息；运行项目 oracle/checker 后再生成中间视图或 final table。headline number 必须能回到远程 run ID 和 raw artifact。正式结论所需产物回传约定存储或由可追溯远程路径提供，不手改远程结果值。
8. **精确收尾**：只对步骤 5 记录且确认归属自己的 PID/job/session 操作；禁止 `pkill python`、`pkill -u`、宽泛 `kill -9` 或清理他人/未知进程。临时缓存只按预先 retention rule 清理；raw evidence、失败日志和支撑结论的 artifact 不因结果不好而删除。记录结束状态、产物位置、清理项和仍在运行/未确认项。

## 门禁

- `[BLOCK]` 非交互认证失败后仍尝试绕过；secret 被写入仓库/日志；目标主机或工作区不在授权 profile；需要越界成本、凭据、生产/公开或不可逆动作；
- `[BLOCK]` 科研 run 自动切本地/CPU/其他 host/backend/model/data/metric/method path，或将 smoke/mock/stub/synthetic 产物升级为 claim、GO、paper evidence；
- `[BLOCK]` 主机/repo/environment identity、PID/job、日志或 raw artifact 不足以复核声称的运行；
- `[BLOCK]` 批量杀进程、写系统/他人目录、覆盖或删除支撑结论/失败事实的 evidence；
- `[HUMAN]` 仅在步骤 1 的 mandatory 条件出现时等待；已冻结的默认 host、卡范围、workspace 和有限预算使用 autonomous checkpoint；
- `[SCAN]` 执行脚本禁止 `sshpass`、明文密码、`pkill`、用户级/broad kill、未声明设备和 evidence-bearing 自动 fallback；
- `[REVIEW]` 必问：“这个 run 是否在授权 host/workspace/resource 内？失败时是否停止？表中数字能否回到该 PID/job 对应的 raw artifact？”

## 完成判定

- remote work packet 与 checkpoint 类型有记录，实际 host/workspace/resource 未越界；
- 非交互认证、资源、repo 与环境预检通过，或相关动作诚实停在 `BLOCKED`；
- 已启动任务的命令、PID/job/session、日志、状态、成本和产物位置可查；
- smoke 与正式 evidence 物理/语义分离，科研路径未发生自动 runtime fallback；
- oracle/checker 结论与 raw artifact 保留，收尾只影响自己的明确进程和允许清理的临时数据。

## 失败处理

认证、资源、环境、输入、主机身份或 scientific dependency 不满足时停止相关 run 并记录 `BLOCKED`/失败状态；不得存密码、硬挤共享资源、自动换本地/CPU/backend/host、缩小 claim 或用旧结果继续。若存在保持原 contract 的等价主机或实现，先形成新的显式 work packet 和 run ID；超出既有 profile 时取得 HUMAN 决定。SSH 断连或监控 timeout 时重新查询同一 job 的权威状态，不能默认成功、失败或重复启动。无法确认进程归属时不杀，报告未决状态。

## 产物

一条紧凑 remote job record：checkpoint、host、workspace、repo SHA/dirty state、环境身份、设备与资源上限、evidence class/`paper_eligible`、命令、PID/job/session、开始/结束时间、实际成本、status、日志/raw artifact/checker/结果位置、失败原因与精确清理记录。已有实验系统能承载这些字段时不另建台账。
