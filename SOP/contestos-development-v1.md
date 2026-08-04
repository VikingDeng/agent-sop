# ContestOS 开发项目架构标准 v1

> **文档身份**:本标准是**施工蓝图 + 行为约束**。适用项目中的硬锚(§7)不可违反;与《AI 科研架构标准》《竞赛架构标准》共用同一 base(env / 零fallback / 质量门)。
> **适用范围**:所有"交付一个高质量项目"的开发任务 —— 库/框架、服务、CLI、数据管线、infra 组件、应用,以及黑客松 MVP。
> 主轴:AI infra 场景的 **库型 + infra 组件型**(被深度集成、产品级)。app/service/prototype 作为 recipe 与门禁降档处理。
> **核心命题**:agent 驱动开发,最大风险不是"写不出",而是"写出了不是你要的、但看起来对的代码"。
> **启用方式**:项目属于开发任务时,项目级 `CLAUDE.md` 一行引用本文件并遵守其硬锚。
> **版本与来源**:v1。源文件 `~/Desktop/ContestOS_开发项目架构规范_v1.md`;本仓库收录版与源文件 sha256 一致。

---

## §0 世界观:开发骨架防的是什么

研究骨架防"过拟合/静默降级",竞赛骨架防"台账混乱/门槛作弊"。开发骨架防**经典软件腐烂 + agent 特有腐烂**,后者是重点。

### 0.1 腐烂类型

| 腐烂类型 | 表现 | agent 特有? |
|---|---|---|
| **需求-实现漂移** | 做着做着偏离最初要的东西,没人发现 | 强化(agent 会"合理地"跑偏) |
| **隐性扩范围 scope creep** | agent 顺手加了没要求的功能/抽象层 | **agent 特有** |
| **似是而非的代码** | 能跑、看着对,实则错(幻觉 API、错误假设) | **agent 特有** |
| **上下文断裂** | 跨 session 忘了"为什么这么设计" | **agent 特有** |
| **架构侵蚀** | 分层被打穿、循环依赖、上帝模块 | 经典 |
| **依赖失控** | 随手 import、版本不锁、供应链风险 | 经典 |
| **测试缺失/造假** | 无测试,或测试跟着实现写(自证) | 经典+强化 |
| **文档漂移** | README 和代码说的不是一回事 | 经典 |

### 0.2 核心原则:契约先行(spec-as-contract)

- 研究骨架的 oracle 是"独立参考实现";竞赛骨架的 oracle 是"correctness gate";**开发骨架的 oracle 是 SPEC + 验收标准 + 测试**。
- 开工前必须有一份 agent 承诺的**契约**:做什么、**不做什么(non-goals)**、完成判定标准。agent 每一步对着契约做,而不是对着"感觉"做。
- **反需求(non-goals)是一等公民** —— 明确写"不做 X",专门压制 scope creep。

---

## §1 四轴分型:不做 N 套模板,找"什么在变"

按表层技术栈分(web/后端/CLI)是错的——那是表面。真正驱动结构差异的是四根轴,`PROJECT_TYPE.yaml` 声明取值,base 不变、类型作为 recipe 薄分叉。

```yaml
# PROJECT_TYPE.yaml
artifact:   library | service | cli | pipeline | infra-component | app
consumer:   integrated      # 被代码集成(库/API/服务/组件)
          | human           # 被人直接用(CLI/前端/应用)
lifecycle:  oneshot | long-running
maturity:   prototype | product | throwaway   # 控门禁强度,不改目录结构
```

### 轴一:交付形态(artifact)—— 决定 `delivery/` 和构建

| 类型 | 交付物 | 结构影响 |
|---|---|---|
| library/framework/SDK | 可发布的包 | 版本发布、public API 边界 |
| service/后端 | 可部署镜像 | 部署契约、配置、健康检查(沙箱内只设计不起监听) |
| CLI/工具 | 二进制/可执行 | 命令行契约、退出码 |
| pipeline/ETL | job + 产出数据 | 数据质量断言、幂等、可重跑 |
| **infra-component**(算子库/runtime/调度器/编译器插件) | 库或服务,但**深度嵌入别人系统** | 兼容契约极重、可观测性、性能回归 |
| app | 应用 | UX 验收 |

### 轴二:谁消费它(consumer)—— 决定要不要"稳定性契约"(最关键)

- **integrated(被代码集成)**:**API 稳定性契约是一等公民** —— SemVer、向后兼容、废弃策略、契约测试。改了 public API 不兼容 = 腐烂。
- **human(被人直接用)**:稳定性要求在 UX/命令行,契约更轻。

> AI infra 项目重度落在 integrated 侧,所以 §5 的兼容契约对你是刚需,不是可选。

### 轴三:生命周期(lifecycle)—— 决定可观测性与状态

- **oneshot(跑完就退)**:幂等 + 可重跑 + 产出校验。
- **long-running(长驻)**:logging/metrics/tracing、优雅退出、配置热加载(设计层面,沙箱不真起服务)。

### 轴四:成熟度/时间预算(maturity)—— 只控门禁强度,不改目录结构

同一份骨架,按成熟度关掉/打开门禁档位。**底线永不退让:spec-first + 零fallback + 正确性对拍。**

| 成熟度 | 时间预算 | 减什么 | 保什么(底线) |
|---|---|---|---|
| **prototype**(黑客松 MVP) | 小时~天 | 完整测试覆盖、向后兼容、可观测性 | spec-first、零fallback、能跑起来+能 demo |
| **product**(日常交付) | 周~月 | 不减 | 全部 |
| **throwaway**(一次性脚本) | 分钟~小时 | 减到只剩正确性对拍 + 可重跑 | 正确性 |

---

## §2 完整目录树

复用共享 base(env / 零fallback / 质量门),开发特有的挂 `spec/ contracts/`。

```
project/
  PROJECT.md                    # 一句话价值 + 边界 + 非目标
  PROJECT_TYPE.yaml             # 四轴声明(artifact×consumer×lifecycle×maturity)

  spec/                         # ← 契约先行的核心
    REQUIREMENTS.md             # 需求 + 验收标准(每条可测)
    NON_GOALS.md                # 明确不做什么(压 scope creep)
    ARCHITECTURE.md             # 分层/模块边界/依赖方向(人工定稿)
    DECISIONS.md                # ADR:每个关键决策记 why(防上下文断裂)

  contracts/                    # ← 模块/对外接口契约(先定接口再实现)
    <module>.api.md
    CONTRACT.md                 # integrated 项目:SemVer/兼容/废弃策略(见 §5)

  src/<pkg>/                    # 按 ARCHITECTURE 分层,依赖方向单向
    <layer_a>/
    <layer_b>/

  tests/
    unit/  integration/  e2e/
    acceptance/                 # 对着 REQUIREMENTS 写的验收测试(不跟实现写)
    contract/                   # integrated 项目:契约测试(见 §5)
    regression/                 # 性能/行为回归(infra 组件重点)

  env/                          # 复用共享 base(uv/lock/verify_env)
  scripts/
  docs/
    CHANGELOG.md
    README.md

  delivery/
    RUN.md                      # 怎么可复现地跑起来
    PITCH.md                    # 黑客松/prototype:problem-fit/完成度/演示脚本

  recipe/                       # 类型薄分叉(按 artifact 挂)
    library/
    infra-component/
    service/
    cli/
    pipeline/
    app/
```

### 逐节点防腐职责(关键节点)

- **`PROJECT.md` / `spec/`**:契约层。没有它,agent 就是对着感觉编。`NON_GOALS.md` 单独成文是刻意的——把"不做什么"提到和"做什么"同等地位。
- **`spec/DECISIONS.md`(ADR)**:每个关键决策记 why。这是**对抗 agent 上下文断裂**的手段:下一个 session/下一个 agent 读 ADR 就知道"为什么当初不这么做"。
- **`contracts/`**:接口先于实现。integrated 项目的 `CONTRACT.md` 是命脉。
- **`tests/acceptance/`**:**对着 REQUIREMENTS 写,不对着实现写** —— 防"测试跟着实现自证"。
- **`tests/regression/`**:infra 组件的性能/行为回归门,防"改一处、悄悄慢了/变了"。

---

## §3 agent 驱动的三道防线(本骨架关键)

### 防线 1 — spec gate(开工前)

没有 `REQUIREMENTS.md` + `NON_GOALS.md` + 每条可测的验收标准,**不许写实现代码**。
- agent 先产契约 → 人工/自动核对 → 再动手。
- [HUMAN] 只在此处 + `ARCHITECTURE.md` 定稿处介入。

### 防线 2 — drift check(过程中)

每个 PR/提交对照 REQUIREMENTS 自查:
- **"这个改动对应哪条需求?"** 对不上 = 可疑的 scope creep。
- **"有没有引入 NON_GOALS 里的东西?"** 越界即拦。
- **"有没有新增未声明的依赖/抽象层?"** agent 最爱顺手加抽象。
- 强制程度:`product` 每次提交扫;`prototype` 里程碑扫。

### 防线 3 — acceptance test(交付前)

- 测试对着 SPEC 写,不对着实现写(防自证)。
- **零 fallback 铁律**照旧(见 §6)。
- 架构依赖方向用工具扫(禁循环依赖、禁打穿分层)。
- integrated 项目:契约测试 + 兼容性检查必过(见 §5)。

---

## §4 似是而非代码的防治(agent 特有)

agent 会写出"能跑、看着对、实则错"的代码(幻觉 API、错误假设、边界漏判)。对策:

1. **独立 oracle 验证**:关键逻辑用独立参考(差分测试/解析解/已知答案)对拍,不用被测代码自证——与研究/竞赛骨架同一套 oracle 思想。
2. **API 真实性校验**:agent 调用的外部/上游 API,必须有一条真实调用的 smoke test 证明"这个 API/签名真的存在且行为如此",禁止只靠类型/文档假设。
3. **边界与错误路径必测**:acceptance/unit 覆盖空输入、极端 shape、并发、错误码——似是而非的代码通常在 happy path 之外崩。
4. **禁止无声假设**:关键假设写进 `DECISIONS.md` 或断言进代码(fail fast),不留隐性前提。

---

## §5 integrated 项目的稳定性契约(库型 + infra 组件重点)

被代码集成的项目,public API 就是产品。`contracts/CONTRACT.md` 是一等公民。

### 5.1 CONTRACT.md 应含

- **public API 表面冻结**:哪些是 public(受兼容保护)、哪些是 internal(可随意改)。物理上用命名/目录/`__all__` 区分。
- **SemVer 策略**:major=破坏兼容 / minor=加功能兼容 / patch=修 bug。破坏兼容必须 major bump + 迁移说明。
- **废弃策略(deprecation)**:先标废弃 + 保留 N 个版本 + 给迁移路径,再删除。禁止直接删 public API。
- **行为契约**:不只是签名,还有语义(幂等性、错误码、副作用、性能量级承诺)。

### 5.2 契约测试(tests/contract/)

- 锁住 public API 的签名 + 行为,任何不兼容改动让契约测试**红**,逼出 major bump 或回退。
- infra 组件额外:**性能回归门**(tests/regression/)—— 关键路径的延迟/吞吐/显存立基线,劣化超阈值即拦。这与《竞赛架构标准》的 profiling 思想一致,但目标是"防止悄悄变慢",不是"爬榜"。

### 5.3 深度集成边界

infra 组件嵌入别人系统时:
- 用 `src/adapters/` 把"对接宿主系统"的代码集中,不散落。
- 对宿主的假设(版本、能力)写进 `CONTRACT.md`,并用 `verify_env.py` 式自检在启动时校验(校验失败即 raise,不降级)。

---

## §6 零 fallback 铁律(开发版)

沿用研究/竞赛骨架。开发场景强调:

### 6.1 禁止模式

- `try: ... except: pass` / `except: return default` —— 吞异常。
- `except: <降级路径>` —— 出错走另一条路悄悄产出结果。
- `if not available: <fallback>` —— capability-probe 降级。
- `.get(k, default)` 用于**关键配置**时的静默默认。
- 库型项目额外:**禁止对调用方错误静默兜底** —— 参数非法就 raise,不"猜"调用方想要什么。

### 6.2 唯一例外

外部网络/API/IO(下载、拉取、跨服务调用)可 bounded retry,**重试耗尽后必须 raise**,不得静默返回空/默认。

### 6.3 门禁

`gate_no_fallback.py` 正则扫 `except\s*:`、`except[^:]*:\s*(pass|return|continue)`、可疑 `.get(...)`、`is_available()`/`is_supported()` 后跟 else。
[REVIEW] 必问:**"有没有任何路径,在出错/资源不满足时不报错而是继续产出结果?"**

---

## §7 硬锚表 + enforcement 分级

| 锚点 | 检查 | 分级 | 成熟度门槛 |
|---|---|---|---|
| spec 齐全才能写实现 | REQUIREMENTS+NON_GOALS+验收标准存在 | [AUTO] | 全档(throwaway 可压缩为一页) |
| 改动可追溯到需求 | drift check | [REVIEW] | product 每次 / prototype 里程碑 |
| 无 NON_GOALS 越界 | drift check | [REVIEW] | product+ |
| 无 fallback/降级 | gate_no_fallback.py | [SCAN]+[REVIEW] | **全档(底线)** |
| 验收测试对着 spec | 人工/结构核对 | [REVIEW] | product+ |
| 依赖方向单向、无循环 | import 图扫描 | [SCAN] | product+ |
| public API 兼容 | 契约测试 | [AUTO] | integrated+product |
| 性能不回归 | regression 基线 | [AUTO] | infra-component |
| 依赖锁定 | uv.lock 存在 | [AUTO] | product+ |
| 能可复现跑起来 | RUN.md + smoke | [RUNTIME] | **全档(底线)** |
| ARCHITECTURE/ADR 定稿 | 文件更新 | [HUMAN] | product+ |

分级:`[AUTO]` 自动阻断 / `[SCAN]` 静态扫 / `[REVIEW]` 评审追问 / `[RUNTIME]` 运行时 / `[HUMAN]` 人工。人工只在 spec/架构定稿处介入。

---

## §8 scaffold 施工顺序(10 步)

1. 写 `PROJECT.md`(价值 + 边界)+ `PROJECT_TYPE.yaml`(四轴)。
2. 写 `spec/REQUIREMENTS.md`(每条可测)+ `spec/NON_GOALS.md`。**spec gate:没这些不许写实现。**
3. 写 `spec/ARCHITECTURE.md`(分层 + 依赖方向),人工定稿。
4. integrated 项目:写 `contracts/CONTRACT.md`(public API 表面 + SemVer + 废弃策略)。
5. 复用共享 base:`env/`(uv + lock + verify_env)。
6. 按 ARCHITECTURE 建 `src/<pkg>/` 分层骨架(空实现 + 接口)。
7. 先写 `tests/acceptance/`(对着 REQUIREMENTS)——**测试先于实现或并行,不追着实现写**。
8. 实现 `src/`,每次提交跑 drift check(对照需求 + non-goals)。
9. 装门禁(§7):零fallback 扫、依赖图扫、契约测试、性能回归(按成熟度开档)。
10. 写 `delivery/RUN.md`;prototype 补 `delivery/PITCH.md`;`DECISIONS.md` 落关键决策。

---

## §9 recipe 速查(按 artifact × 你的重心)

| 场景 | artifact×consumer×lifecycle×maturity | recipe | 写多深 |
|---|---|---|---|
| **CUDA 算子库 / runtime**(你的主战场) | infra-component × integrated × oneshot/long × product | `infra-component`+`library` | **最深**:CONTRACT + 契约测试 + 性能回归门 + adapters 边界 |
| Python SDK / 框架 | library × integrated × * × product | `library` | 深:CONTRACT + SemVer + 契约测试 |
| 内部服务/后端 | service × integrated × long-running × product | `service` | 中:部署契约 + 可观测性 + 优雅退出 |
| CLI 工具 | cli × human × oneshot × product | `cli` | 中:命令行契约 + 退出码 |
| 数据/ETL 管线 | pipeline × integrated × oneshot × product | `pipeline` | 中:幂等 + 数据质量断言 + 可重跑 |
| **黑客松 MVP / Agent App** | app × human × * × **prototype** | `app` | 底线档:spec 一页 + 零fallback + 能 demo + PITCH.md |
| 一次性脚本 | * × * × oneshot × **throwaway** | 无 recipe | 最薄:正确性对拍 + 可重跑 |

---

## §10 与其他骨架的边界

- **黑客松/应用赛**:归属本骨架的 `app × prototype` 档,门禁降到底线(spec-first + 零fallback + 能 demo),挂 `delivery/PITCH.md`。《竞赛架构标准》里只留提交打包薄壳。
- **AI 科研骨架**(《AI 科研架构标准》):方法/实验为核心,oracle=独立参考实现,防过拟合/静默降级。
- **竞赛骨架**(《竞赛架构标准》):客观分为核心,oracle=correctness gate,防台账混乱/门槛作弊。
- **本骨架**:交付为核心,oracle=SPEC+验收测试,防需求漂移/scope creep/似是而非代码。
- **共享 base(三骨架不减)**:env 锁 + 零fallback 铁律 + 独立 oracle 验证思想 + enforcement 分级 + ADR。
