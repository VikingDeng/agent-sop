# ContestOS 竞赛项目架构标准 v1

> **文档身份**:本标准是**施工蓝图 + 行为约束**。适用项目中的硬锚(§8)不可违反;与《AI 科研架构标准》(contestos-ai-research-v1.md)共用同一 base(env / registry / manifest / gate)。
> **适用范围**:**有客观分且能被本地代理**的竞赛项目(性能赛 / 系统优化赛 / 榜单预测赛)。
> 主轴:AI infra 性能赛 + 系统优化赛;榜单预测(Kaggle 型)作为 recipe。
> **不适用**:靠评委 rubric 打分的黑客松/应用赛 —— 那是"限时项目开发",走**开发骨架**(后续 SOP) + `PITCH.md`,竞赛骨架里只留薄壳。
> **启用方式**:项目属于竞赛类型时,项目级 `CLAUDE.md` 一行引用本文件并遵守其硬锚;从 `contestos-starter` 的 `contests/` 结构开工。
> **版本与来源**:v1。源文件 `~/Desktop/ContestOS_竞赛项目架构规范_v1.md`;本仓库收录版与源文件 sha256 一致。

---

## §0 世界观:竞赛按"赛制机制"分类,不按学科

竞赛骨架的第一原则:**结构由判分机制决定,不由题目学科决定**。同一学科(比如"写个 CUDA kernel")在不同赛制下防腐点完全不同。

### 0.1 四类赛制机制

| 类型 | 判分方式 | 提交形态 | 关键约束 | 是否进本骨架 |
|---|---|---|---|---|
| ① 榜单预测赛 (Kaggle 型) | private LB 客观分 | CSV 提交 / code competition(断网+推理时限) | 过拟合 public LB;code 赛资源/时限硬约束 | ✅ recipe |
| ② Kernel/性能赛 (GPU MODE / Ascend C / AMD) | **先正确性门槛,再排速度**,平台侧计时 | 提交 kernel 源码 / patch | correctness gate 不可作弊;性能可复现 | ✅ **主轴** |
| ③ 系统/优化赛 (AICAS 等) | 多目标:精度 × 延迟 × 显存 | 提交系统/模型工件 | Pareto 权衡;多指标同源 | ✅ **主轴** |
| ④ 黑客松/应用赛 | 评委 rubric(problem-fit/完成度/演示) | 项目 + demo | 无可复现客观分 | ❌ 走开发骨架 |

### 0.2 竞赛骨架的两条原则(区别于研究骨架)

1. **本地代理优先(local proxy first)**:线上榜/评测机是慢反馈、有次数限制的黑箱。竞赛工程的核心资产是 `bench/` —— 把线上分**在本地复刻成可无限跑的客观分**。没有本地代理分,就是在盲赌提交次数。
2. **正确性是门槛,不是指标(correctness is a gate, not a score)**:性能赛/系统赛里,速度分只有在正确性通过后才有意义。correctness gate 用**独立 oracle** 判定,禁止被测代码自证。

---

## §1 腐烂类型 → 物理结构

竞赛骨架防的腐烂和研究骨架不同。逐类型对应到物理隔离手段。

| 腐烂类型 | 表现 | 物理结构对策 |
|---|---|---|
| **提交台账混乱** | 记不清哪次提交对应哪个 commit / 什么 idea / 得了多少分 | `submissions/<sub_id>/` + `SUBMISSION_LEDGER.md`,无 commit 绑定的提交不算数 |
| **patch 与上游纠缠** | 在别人仓库里散改,分不清自己改了啥,上游一升级全丢 | `upstream/<repo>@<commit>/`(只读) + `patches/`(patch series) |
| **本地分/榜分脱节** | 本地跑一版、提交另一版,gap 无法解释 | 同一 commit 强制既出本地分又出提交产物;gap 进台账 |
| **过拟合 public LB** | public 榜爬得高,private 榜崩 | `bench/` 强制 local holdout;probe 次数进台账 |
| **正确性门槛作弊** | 用被测代码自证"我对了" | correctness gate 用独立 oracle(参考实现/解析解) |
| **静默降级骗分** | kernel 不支持某 case 时静默 fallback 到慢/torch 路径 | 零 fallback 铁律(见 §7),`if not supported: fallback` 直接禁 |
| **profile 丢失** | 优化做完了,但拿不出证据说明快在哪 | `profiling/` 绑定每次提交,nsys/ncu/rocprof 产物归档 |
| **多赛/多平台错位** | 同时打几个赛,产物混在一起 | 每个赛一个独立 contest 实例目录(见 §2) |

---

## §2 完整目录树

一个竞赛实例 = 一个独立目录(多赛并行时物理隔离)。顶层 `contests/<contest_name>/`。

```
contests/<contest_name>/          # 一个赛一个目录,多赛物理隔离
  CONTEST.md                      # 赛制卡:类型/判分规则/提交格式/次数限制/截止/资源约束
  RULES_SNAPSHOT.md               # 官方规则原文快照(截止日/断网/时限/允许的外部资源)
  code_form.yaml                  # 声明本赛 code 形态: patch | clone | scratch

  env/                            # ← 复用共享 base(见研究骨架 §4)
    setup_env.sh
    Dockerfile
    verify_env.py
    env.lock.json

  upstream/                       # ← code 形态 A/B 专用:锁死上游
    <repo>@<commit>/              # vendored 上游快照,只读基线
    patches/                      # 形态 A:你的改动以 patch series 存
      0001-<desc>.patch
      0002-<desc>.patch
    PROVENANCE.md                 # 上游 repo URL / commit / license / apply 步骤

  src/<pkg>/                      # 形态 B/C:你自己的代码(适配层对接上游,不散改)
    solution/                     # 参赛解法主体
    adapters/                     # 对接上游/评测机的适配边界
    oracle/                       # 独立正确性参考实现(对拍用,不进提交产物)

  bench/                          # ← 本地榜单代理(核心资产)
    correctness/                  # correctness gate:独立 oracle 对拍
      test_cases.yaml             # 测试用例(含边界/极端 case)
      run_correctness.py          # 返回 pass/fail,失败即作废
    speed/                        # 速度/多目标测量
      run_bench.py                # 复刻线上计时口径(warmup/repeat/取中位数)
      metrics.yaml                # 测哪些指标:latency/throughput/mem/accuracy
    holdout/                      # 榜单预测赛:local holdout,防过拟合 public LB
    LEADERBOARD_PROXY.md          # 本地代理与线上榜的口径对齐说明 + gap 记录

  profiling/                      # ← 性能证据归档
    <sub_id>/
      nsys/ ncu/ rocprof/         # 平台对应 profiler 产物
      roofline.md                 # roofline / 瓶颈分析
      timeline.md                 # 关键 kernel 时序

  submissions/                    # ← 提交台账
    SUBMISSION_LEDGER.md          # 一行一提交(见 §4 模板)
    <sub_id>/
      manifest.json               # code_form/upstream_commit/git_sha(dirty=false强制)
      submitted_files/            # 实际提交上去的文件快照(所见即所提)
      local_score.json            # bench 本地代理分
      leaderboard_score.json      # 回填的线上分(可后补)
      IDEA.md                     # 这次赌的优化假设是什么

  recipe/                         # 赛制薄分叉(不做四套模板)
    kernel/                       # ② GPU MODE / Ascend C / AMD
    system/                       # ③ AICAS 多目标
    leaderboard/                  # ① Kaggle 型
  scripts/
  results/                        # 只收 dirty=false 且 correctness=pass 的正式结果
  docs/
    STRATEGY.md                   # 打法/假设账本
    DECISIONS.md                  # 关键决策记录
```

### 逐节点防腐职责(关键节点)

- **`CONTEST.md` / `RULES_SNAPSHOT.md`**:赛制是结构的输入。断网、推理时限、允许的外部资源、提交次数上限,全部先落地成文,再开工。规则会变,所以存快照 + 日期。
- **`code_form.yaml`**:一个赛的 code 形态先声明清楚,决定 `upstream/` 还是 `src/` 是主战场。
- **`upstream/`**:形态 A/B 的命脉。上游永远只读、锁 commit;你的东西以 patch 或独立 src 存在,永远可分离。
- **`bench/`**:竞赛工程最重的资产。`correctness/` 是门,`speed/` 是分,`holdout/` 防过拟合。
- **`src/oracle/`**:独立正确性参考,**绝不进提交产物**,只用于对拍。放这里是为了物理上和 `solution/` 分开,防止用被测代码自证。
- **`submissions/`**:每次提交是一个不可变快照。`submitted_files/` 存"所见即所提",杜绝"本地一版提交另一版"。

---

## §3 code 形态轴:patch / clone / from-scratch

这是竞赛骨架相对研究骨架**新增的核心结构维度**。三种形态物理结构不同、防腐点不同,由 `code_form.yaml` 声明,由 `upstream/` 机制统一治理。

### 3.1 形态 A —— patch(在别人仓库上改)

最容易腐烂:改着改着分不清哪些是你的、哪些是上游的,上游一升级或重置一次全丢。

```
upstream/
  <repo>@<commit>/        # vendored,锁死上游 commit,只读基线
  patches/
    0001-<desc>.patch     # git format-patch / quilt 生成
    0002-<desc>.patch
  PROVENANCE.md
```

**铁律:改动只以 patch 存在,不直接 commit 到 vendored 树。**

- 你的贡献永远和上游可分离、可重放、可随上游升级 rebase。
- 提交打包 = `vendored 快照` apply `patches/*` 得到最终产物。
- `PROVENANCE.md` 记:上游 repo URL、锁定 commit、license、如何 apply(应对 code 赛"提交 patch"的场景)。
- manifest 记 `code_form: patch` + `upstream_commit`。

### 3.2 形态 B —— clone-their-repo(基于官方 starter repo 整体开发)

比赛给一个 starter/baseline repo,你在其上做大量开发。

- 上游作为**子模块或 vendored 快照锁 commit**,作为只读基线。
- 你的代码放独立 `src/<pkg>/`,通过 `adapters/` 适配层对接上游 —— **禁止散落 monkey-patch**。
- 需要改上游文件时,仍走 `patches/`(和形态 A 同机制),不直接改 vendored 树。
- manifest 记 `code_form: clone` + `upstream_commit`。

### 3.3 形态 C —— from-scratch(重头写)

标准骨架:`src/<pkg>/solution/` 自己的实现。

- 上游(若有参考实现)只作为 `src/oracle/` 的对拍参考,**不进提交产物**。
- manifest 记 `code_form: scratch`,`upstream_commit: null`。

### 3.4 三形态共用铁律

> **提交产物必须能从 `git_sha + upstream_commit + patches` 完全重建。**

任何一次提交,给定这三样应能字节级复现出 `submitted_files/`。做不到 = 台账失效。

---

## §4 提交台账(submissions/)

性能赛的"分"不是一个标量,是**一组证据**。台账把每次提交的证据链绑死。

### 4.1 `SUBMISSION_LEDGER.md` 模板

```markdown
| sub_id | 时间 | commit | code_form | 本地分 | 榜分 | gap | correctness | idea | 状态 |
|--------|------|--------|-----------|--------|------|-----|-------------|------|------|
| s0007  | 08-04 | a1b2c3d | patch | 1.83ms | 1.91ms | +4.4% | pass | 双缓冲+向量化load | 已提交 |
| s0006  | 08-03 | 9f8e7d6 | patch | 2.10ms | -     | -     | FAIL  | shared mem tiling | 作废(未过门槛) |
```

- **无 `sub_id` + commit 绑定的提交不算数。**
- **`correctness=FAIL` 的提交作废**,不进正式行,不占提交次数账(但记录以防重复踩坑)。
- **`gap`(本地 vs 线上)必须记录**;gap 异常大 = 本地代理失真,是要修的 bug,不是可忽略的噪声。

### 4.2 `submissions/<sub_id>/manifest.json` 模板

```json
{
  "sub_id": "s0007",
  "timestamp": "2026-08-04T14:22:00+08:00",
  "git_sha": "a1b2c3d",
  "git_dirty": false,
  "code_form": "patch",
  "upstream_commit": "e5f6a7b8",
  "patches": ["0001-double-buffer.patch", "0002-vectorized-load.patch"],
  "local_score": {"latency_ms_p50": 1.83, "correctness": "pass"},
  "leaderboard_score": {"latency_ms": 1.91, "rank": 12},
  "gap_pct": 4.4,
  "profile_ref": "profiling/s0007/",
  "idea_ref": "submissions/s0007/IDEA.md",
  "env_lock": "env/env.lock.json",
  "status": "submitted"
}
```

**铁律:`git_dirty=true` 或 `correctness!=pass` → 禁止进入正式提交与 `results/`。**

### 4.3 三条竞赛版铁律

1. **正确性门槛先过再谈速度**:`bench/correctness/` 必须先跑对拍 oracle,`correctness=pass` 才允许记 speed 分。这与 GPU MODE / KernelBench 的"先 correctness gate 再排速度"一致。
2. **本地分与榜分同源**:同一 commit 既出本地分又出 `submitted_files/`。禁止"本地跑一版、提交另一版"。
3. **零 fallback(竞赛版)**:kernel/系统解法里禁止 `if not supported: fallback to torch/slow path` —— 性能赛里静默回退慢路径 = 分数造假(本地代理测不到真实提交路径)。详见 §7。

---

## §5 本地榜单代理(bench/)

`bench/` 是竞赛工程的核心资产。目标:**把线上黑箱榜复刻成本地可无限跑的客观分**。

### 5.1 correctness gate(门)

- 用 `src/oracle/` 的**独立参考实现**对拍(差分测试),或用解析解/已知答案。
- 覆盖边界 case、极端 shape、数值稳定性 case —— 平台隐藏用例往往卡这些。
- 返回二值 `pass/fail`;fail 即该提交作废。
- **禁止**用被测代码(`solution/`)自证正确。

### 5.2 speed / 多目标测量(分)

- **复刻线上计时口径**:warmup 次数、repeat 次数、取中位数还是均值、是否含 H2D/D2H —— 与官方口径对齐,写进 `LEADERBOARD_PROXY.md`。
- 系统赛(③)测多目标:latency × throughput × memory × accuracy,输出 Pareto 点而非单值。
- 测量与正确性**同源**:同一 build、同一输入。

### 5.3 holdout(防过拟合,榜单预测赛专用)

- 榜单预测赛(①)强制 local holdout,本地代理分要能预测 private LB 趋势。
- probe public LB 的次数进台账 —— 每次 probe 都是过拟合风险。

### 5.4 `LEADERBOARD_PROXY.md`

记录本地代理与线上榜的**口径对齐**:测量方法、硬件差异、已知 gap 来源、历次 gap 数值。gap 收敛程度 = 本地代理可信度。

---

## §6 性能证据(profiling/)

每次值得记录的提交都绑一份 profile,证明"快在哪、瓶颈在哪"。

- **平台对应 profiler**:NVIDIA → nsys/ncu;AMD → rocprof;Ascend → 对应 profiler。产物按 `profiling/<sub_id>/` 归档。
- **`roofline.md`**:判断是 compute-bound 还是 memory-bound,决定下一步优化方向。
- **`timeline.md`**:关键 kernel 时序,找 gap/stall/串行化点。
- 与《AI 科研架构标准》§9.4 效率哲学一致:**先 profile 再优化**,吃满卡(高 GPU util / 接近 roofline)即达标;只有 profile 显示 CPU 卡点 / 可缓存复用 / 可预处理时才继续优化。**禁止用降级换速度**(质量数与吞吐数必须同一 run 产出)。

---

## §7 零 fallback 铁律(竞赛版)

沿用《AI 科研架构标准》§9.2(零 fallback / 零静默降级),竞赛场景强化:**性能赛里静默 fallback = 分数造假**。

### 7.1 禁止模式

- `try: fast_kernel() except: torch_fallback()` —— 静默回退慢路径。
- `if not is_supported(shape): return slow_path()` —— capability-probe 降级。
- `except: pass` / `except: return default` —— 吞异常。
- `.get(k, default)` 静默默认值(用于关键配置时)。

### 7.2 唯一例外

外部网络/API(如下载数据集、拉上游 repo)可 bounded retry,但**重试耗尽后必须 raise**,不得静默返回空/默认。

### 7.3 门禁

`gate_no_fallback.py` 正则扫:`except\s*:`、`except[^:]*:\s*(pass|return|continue)`、可疑 `.get(...)`、`is_available()`/`is_supported()` 后跟 else 分支。
[REVIEW] 必问:**"有没有任何路径,在出错/资源不满足/case 不支持时不报错而是走了另一条(慢/降级)路径产出结果?"**

---

## §8 硬锚表 + enforcement 分级

| 锚点 | 检查 | 分级 |
|---|---|---|
| `git_dirty=false` 才能提交 | manifest.git_dirty | [AUTO] pre-submit hook |
| `correctness=pass` 才记 speed | bench gate 输出 | [AUTO] |
| 提交产物可从 sha+upstream+patches 重建 | 重建校验 | [SCAN] |
| 无 fallback/降级路径 | gate_no_fallback.py | [SCAN]+[REVIEW] |
| 本地分/榜分同源同 commit | manifest 交叉校验 | [AUTO] |
| gap 记录且异常 gap 触发排查 | LEADERBOARD_PROXY.md | [REVIEW] |
| patch 不直接 commit vendored 树 | upstream/ 只读校验 | [SCAN] |
| CONTEST.md/RULES_SNAPSHOT.md 齐全 | 文件存在 | [AUTO] |
| 打法/假设账本 | STRATEGY.md 更新 | [HUMAN] |

enforcement 分级:`[AUTO]`(自动阻断) / `[SCAN]`(静态扫描) / `[REVIEW]`(评审追问) / `[RUNTIME]`(运行时断言) / `[HUMAN]`(人工把关)。人工只在 `CONTEST.md`/`STRATEGY.md` 定稿处介入。

---

## §9 scaffold 施工顺序(10 步)

1. 建 `contests/<contest_name>/`,写 `CONTEST.md` + `RULES_SNAPSHOT.md`(赛制/判分/次数/时限/断网/资源约束)。
2. 定 `code_form.yaml`(patch / clone / scratch),决定 `upstream/` 还是 `src/` 为主战场。
3. 复用共享 base:`env/`(uv + torch-backend + verify_env + env.lock.json)。
4. 形态 A/B:拉上游锁 commit 进 `upstream/<repo>@<commit>/`,写 `PROVENANCE.md`;形态 C:建 `src/<pkg>/solution/`。
5. 建 `src/oracle/` 独立参考实现(对拍用)。
6. 建 `bench/correctness/`(门)—— **先能判对错,再谈优化**。
7. 建 `bench/speed/`(分),对齐线上计时口径,写 `LEADERBOARD_PROXY.md`。
8. 建 `submissions/` + `SUBMISSION_LEDGER.md`,跑通"一次提交"的完整流水(manifest + submitted_files + local_score)。
9. 接 `profiling/`,让每次提交能出 profile 证据。
10. 装门禁(§8),`STRATEGY.md` 落第一版打法假设。

---

## §10 与其他骨架的边界

- **黑客松/应用赛**:无客观分 → 不进本骨架。工程走**开发骨架**,竞赛侧只留一份 `PITCH.md` + 提交打包薄壳。
- **AI 科研骨架**(《AI 科研架构标准》):共用 base(env/registry/manifest/gate/零fallback/效率哲学)。区别:科研骨架防"过拟合私榜 + 静默降级 + 实验管理混乱";竞赛骨架额外防"提交台账混乱 + 正确性门槛作弊 + 本地榜脱节 + patch 与上游纠缠"。
- **多赛并行**:每个赛一个 `contests/<name>/` 独立实例,物理隔离,共享 base 通过 env 复用。

---

## 附录:赛制 → recipe 映射速查

| 你的赛 | 类型 | recipe | code 形态倾向 | bench 重点 |
|---|---|---|---|---|
| GPU MODE Kernel Leaderboard | ② | `recipe/kernel/` | patch/scratch | correctness gate + 平台计时口径 |
| AMD Developer Challenge | ② | `recipe/kernel/` | scratch/clone | correctness + roofline |
| 华为 Ascend C 算子赛 | ② | `recipe/kernel/` | scratch | 昇腾 profiler + 精度门槛 |
| 天池 AICAS 软硬协同 | ③ | `recipe/system/` | clone | 多目标 Pareto(精度×延迟×显存) |
| PAC 并行应用挑战赛 | ③ | `recipe/system/` | clone/patch | 扩展性 + 多节点计时 |
| Kaggle / AIMO / ARC | ① | `recipe/leaderboard/` | scratch | local holdout 防过拟合 |
