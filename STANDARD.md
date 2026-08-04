# ContestOS · AI 科研项目架构标准 v1

> **文档身份**:本标准是**施工蓝图**,不是设计说明 —— agent 读完应能直接 scaffold 出目录、写出模板文件、配好环境、装好 gate;也是**行为约束** —— 适用项目中的硬锚(§6)不可违反。
> **适用范围**:AI 科研项目(LLM / agent / RL / 推理期方法 / 数据中心),即"贡献往往不是模型本身,而是围绕一个不拥有的骨干模型做的 method"。
> **启用方式**:项目属于该类型时,项目级 `CLAUDE.md` 一行引用本文件(如"开发前先读 STANDARD.md 并遵守其硬锚"),不整体注入。
> **版本与来源**:v1(骨架终稿)。源文件 `~/Desktop/ContestOS_AI科研项目架构规范_v1.md`;本仓库收录版与源文件 sha256 一致。模板落地见 `contestos-starter` 仓库。

## 读法

每一个目录节点都标注了它**防住哪一种具体的腐烂/造假**;答不出的节点即为装饰,不要建。

---

## 0. 世界观:AI 科研有 4 种模式,骨架必须同时容纳

| 模式 | 贡献形态 | 训不训练 | 例子 | 启用的 recipe |
|---|---|---|---|---|
| **A 从零训练** | 新架构/新损失/新预训练 | 是,重 | 新 attention、新 SSM | `recipe/from_scratch/` |
| **B 后训练/微调** | SFT / DPO / RLHF / RL 配方 | 是,轻~中 | 对齐、推理增强、领域适配 | `recipe/finetune/`、`recipe/rl/` |
| **C 推理期方法** | prompting / decoding / logit 处理 / agent scaffold / 检索 / 搜索 | 否(骨干冻结) | CoT 变体、约束解码、agent 框架、test-time search | `recipe/inference/` |
| **D 数据中心** | 数据构造/清洗/合成配方 | 可有可无 | 合成数据、课程学习、去污 | 任一 recipe + `src/data/synthesize.py` |

**第一原则:method 是一等公民,model 是被锁定的外部依赖。** 你的创新在骨干**之外**,骨干(Llama/Qwen/…)是带版本锁的依赖,不是产出。

**第二原则:不拆成多个仓库/模板,用「一个 base 骨架 + `recipe/` 薄分叉」。**
依据:verl 用顶层 `recipe/` 目录承载不同算法配方,共用底层 `verl/` 包;OpenRLHF 把 SFT/DPO/PPO/RM 全塞进一套 CLI 靠参数切换,而非拆多仓库。三种模式(rollout / 微调 / 做 logit)共享同一套地基(骨干加载、registry、评测 harness、环境锁、manifest、污染检测),只有中间算法逻辑一层不同,这层用 `recipe/` 承载。地基永远一份,改一处不必同步多处。

---

## 1. 腐烂类型 → 物理结构映射表(设计约束来源)

科研代码的腐烂是**科学性**的(不是工程性的)。骨架的每个结构都要能追溯到这张表的某一行。

### 1.1 通用科研腐烂(4 类)

| 腐烂方式 | 表现 | 骨架用什么挡 |
|---|---|---|
| 探索污染生产 | notebook 里改改跑跑,结论就写进论文,没人能复现 | `notebooks/`(throwaway)与 `src/`(locked)物理隔离;`src` 禁 import `notebooks` |
| 评测污染训练 | 在 test 上调参/早停看 test/数据泄漏 | split 冻结+哈希;`eval` 不 import `train`;test 只在最后开封一次 |
| 静默降级 | 指标算不出就跳过、baseline 抄论文数、单 seed 当结论 | 指标缺失=硬失败;baseline 本地复现;多 seed 强制 |
| 灌水/挑好结果 | 只留跑赢的实验,删负结果,cherry-pick seed | run 目录不可覆盖 + `HYPOTHESIS_LEDGER` 预注册指标+保留负结果 |

### 1.2 LLM/agent 时代新增腐烂(7 类,更隐蔽)

| 新腐烂 | 表现 | 骨架用什么挡 |
|---|---|---|
| 骨干漂移 | 用 `gpt-4`/`Llama-3-8B` 不带版本,过俩月结果变了没人知道 | `registry.yaml` 强制 **revision commit hash + checksum**,不带 revision 拒绝加载 |
| 解码不确定性未记录 | temperature/top_p/seed 没记,别人复现不出 | 每次调用的 sampling params + seed + backend 进 manifest,缺失=硬失败 |
| 评测污染(数据侧) | test 集在骨干预训练里见过,分数虚高 | `contamination.py` 强制检查 + DATA_CARD 标注污染状态 |
| 不公平骨干 | 我方 method 挂强骨干、baseline 挂弱骨干 | Method 与 Baseline 走同一接口、同一骨干矩阵,report 骨干列必须一致 |
| serving 不一致 | vLLM 跑的数 ≠ HF 跑的,混着报 | manifest 记录哪个 backend 产出;禁止跨 backend 拼一张表;一致性容差测试 |
| agent 轨迹不可复现 | 多步 agent 每次走不同路径,报了最好那次 | 记录完整 trajectory + 工具调用 + 随机源,多 seed 报分布 |
| reward hacking(RL 专属) | reward 一路涨但模型退化/KL 爆炸 | reward 曲线 + KL 曲线强制落盘,可审计 |

---

## 2. 完整目录树(逐节点标注防腐职责)

```
ai-research/
├── README.md                       # 30秒:是什么 + 一条命令复现主表
├── ARCHITECTURE.md                 # [HUMAN] 分层/依赖图/边界/被否决方案(动代码前先写)
├── RESEARCH_MODE.md                # 声明本项目是 A/B/C/D 哪种 → 决定启用哪些 recipe/目录
├── pyproject.toml                  # 依赖声明(唯一入口,禁止散落 pip install)
├── uv.lock                         # 精确到 hash 的依赖锁
├── .python-version                 # 3.12(GPU 场景 vLLM 只支持 3.9–3.12)
│
├── env/                            # ★ 独立环境层(AI 复现头号杀手)
│   ├── setup_env.sh                #   唯一入口:建 uv venv → 按驱动装 torch/vllm → 校验
│   ├── Dockerfile                  #   系统层:CUDA/驱动/flash-attn 编译环境
│   ├── verify_env.py               #   [RUNTIME] 装完自检:cuda 可用/vllm 版本/GPU 数/dtype
│   └── env.lock.json               #   跑时快照:nvidia-smi/CUDA/驱动/torch/vllm 版本
│
├── conf/                           # 单一事实源(Hydra 风格组合)
│   ├── config.yaml                 #   顶层默认(组合入口)
│   ├── method/      *.yaml         #   你的方法超参
│   ├── model/       *.yaml         #   选哪个骨干(引用 registry key + revision)
│   ├── task/        *.yaml         #   评哪个任务
│   ├── serving/     *.yaml         #   vLLM: tp_size/dtype/max_len/gpu_mem_util
│   ├── train/       *.yaml         #   模式 A/B 才有
│   ├── rl/          *.yaml         #   RL recipe:算法/advantage/kl coef
│   └── experiment/  *.yaml         #   成套:method × model × task × seed 笛卡尔
│
├── recipe/                         # ★ 薄分叉:不同模式的编排入口,共用 src/ 地基
│   ├── from_scratch/               #   模式 A
│   ├── finetune/                   #   模式 B:SFT/DPO
│   ├── rl/                         #   模式 B:GRPO/PPO/REINFORCE++(四角色编排)
│   └── inference/                  #   模式 C:decoding/logit/agent(骨干冻结)
│
├── src/<pkg>/
│   ├── method/                     # ★ 你的贡献,与骨干解耦
│   │   ├── interface.py            #   abstract Method:method 和 baseline 都实现它
│   │   ├── <your_method>/
│   │   │   ├── components.py        #     真正 novel 的部件
│   │   │   └── recipe.py            #     把骨干 + 组件 装配起来
│   │   └── ablations/              #   你方法的消融变体(≠ baseline)
│   │
│   ├── models/                     # 骨干适配器:method 不关心底层是 HF 还是 vLLM
│   │   ├── backbone.py             #   abstract Backbone: generate()/logprobs()/embed()
│   │   ├── hf_backbone.py          #   本地 transformers 后端
│   │   ├── vllm_backbone.py        #   vLLM 离线批量 / 连 online server
│   │   ├── api_backbone.py         #   远程 API(版本必须 pin)
│   │   └── registry.py             #   读 models/registry.yaml,校验 revision+checksum
│   │
│   ├── rollout/                    # 仅 RL recipe 启用
│   │   ├── generator.py            #   用 vLLM 批量生成轨迹(采样参数进 manifest)
│   │   └── trajectory.py           #   轨迹 schema,可回放
│   ├── reward/                     # 仅 RL recipe 启用
│   │   ├── interface.py            #   abstract Reward
│   │   ├── rule_reward.py          #   规则奖励(如 math verify)
│   │   └── model_reward.py         #   奖励模型(版本 pin)
│   ├── roles/                      # 仅 RL recipe:actor/reference/critic 封装与同步
│   │
│   ├── data/
│   │   ├── datasets.py             #   加载/校验(schema/范围/NaN 早失败)
│   │   ├── loaders.py
│   │   ├── contamination.py        #   ★ 污染检测:test n-gram/embedding 命中骨干语料/训练集
│   │   ├── synthesize.py           #   模式 D:合成数据(生成器模型版本+seed 即"数据源")
│   │   └── splits.py               #   split + split_hash
│   │
│   ├── tasks/                      # ★ 任务 = 数据+指标+协议+prompt,不只是数据
│   │   ├── task.py                 #   abstract Task: load()/prompt()/metric()/protocol
│   │   └── <benchmark>/            #   prompt 模板、few-shot、答案抽取正则、指标
│   │
│   ├── eval/
│   │   ├── metrics.py              #   算不出→raise,禁止返回 0/None 蒙混
│   │   ├── evaluate.py             #   [铁律] 不 import method 内部;吃冻结 test;单入口
│   │   └── judge.py                #   LLM-as-judge:judge 模型版本 pin + 校准集
│   │
│   ├── train/                      # 模式 A/B 启用
│   │   ├── loop.py                 #   只见 train+val,永不碰 test 通道
│   │   └── callbacks.py            #   checkpoint/早停(只看 val)/日志钩子
│   │
│   ├── serving/                    # ★ vLLM
│   │   ├── launch_vllm.sh          #   在自有算力起 vLLM server 的规范脚本
│   │   ├── download_model.py       #   规范下载:带 revision/校验 checksum/写 provenance
│   │   └── health_check.py         #   服务起来先自检(版本/dtype/tp 一致)
│   │
│   ├── viz/                        #   从 metrics.json 出图,禁手绘/手填
│   └── utils/
│       ├── seeding.py              #   set_all_seeds + 确定性开关
│       ├── env_capture.py          #   git sha/pip/CUDA/GPU/vllm 版本/驱动
│       └── run_dir.py              #   创建不可覆盖的时间戳 run 目录
│
├── scripts/                        # 编排入口(薄,只拼装 src,不写业务逻辑)
│   ├── download_models.py          #   按 registry 批量下载+校验
│   ├── run_method.py               #   python scripts/run_method.py experiment=main
│   ├── run_baseline.py             #   同一 harness 跑 baseline
│   ├── evaluate.py                 #   开封 test,结论前只跑一次
│   ├── reproduce.sh                #   [铁律] 一条命令复现主表(CI 跑冒烟版)
│   └── make_report.py              #   聚合 experiments/ → results/
│
├── models/
│   └── registry.yaml               # ★ 骨干唯一事实源(revision+checksum+template)
├── models_cache/                   # 权重落地区([只读] chmod,git 忽略,provenance 追踪)
│   └── <model>@<revision>/
│
├── experiments/                    # run 产出区(git 忽略大文件,manifest 入库,不可覆盖)
│   └── 2026-08-04T14-22_main_qwen2.5-7b_seed0/
│       ├── manifest.json           #   [核心] run 身份证(见 §5)
│       ├── config.snapshot.yaml    #   跑时配置快照(拷贝,非引用)
│       ├── env.lock.json           #   跑时环境快照
│       ├── metrics.json            #   [恒定接口] 结构化指标,report 从这读
│       ├── trajectories/           #   agent/多步方法:完整轨迹+工具调用,可回放
│       ├── rollouts/               #   RL:每步 rollout + reward/KL 落盘,可审计
│       ├── generations/            #   原始模型输出抽样(供人抽查)
│       ├── logs/
│       └── status.json             #   {running|done|crashed};崩溃/dirty 不进 results
│
├── data/
│   ├── raw/                        #   [只读] chmod 后禁改,有 DATA_CARD
│   ├── interim/                    #   中间产物(可重建,git 忽略)
│   ├── processed/                  #   喂模型最终形态 + fingerprint.txt
│   └── DATA_CARD.md                #   来源/许可/split/**污染状态**
│
├── baselines/                      # ★ 其他方法,实现同一 Method 接口
│   ├── <baseline_x>/
│   └── REPRO_REPORT.md             #   [反抄数] 证明本地复现 ≈ 原论文(容差内)
│
├── results/                        # 对外结论区(唯一可写进论文的地方)
│   ├── main_table.md               #   make_report 自动生成,骨干列强制一致,禁手改
│   ├── figures/
│   └── LEADERBOARD.md              #   本项目内所有 run 横向对比
│
├── notebooks/                      # 探索区(throwaway,src 禁 import)
│   ├── README.md                   #   "这里输出永不进 results,只是草稿纸"
│   └── *.ipynb                     #   命名带日期+人
│
├── docs/                           # 过程账本(给人读)
│   ├── HYPOTHESIS_LEDGER.md        #   [反灌水] 预注册指标 + 保留负结果
│   ├── EXPERIMENT_PROTOCOL.md      #   评测协议冻结 + 骨干矩阵 + 多seed + 污染规则
│   └── DECISIONS.md                #   方向性决策与被否决方案
│
├── delivery/                       # 30秒验收门面(给决策者)
│   └── UNIT.md                     #   5 行骨架:做了什么/为什么/证据/对比上次/需拍板吗
│
└── tests/
    ├── test_env.py                 #   环境自检(等价 verify_env)
    ├── test_backbone_contract.py   #   HF 与 vLLM 同输入+同 seed 输出差异在容差内
    ├── test_task_contract.py       #   prompt→抽取→指标 端到端已知样例
    ├── test_contamination.py       #   已知污染样本必须被检出
    ├── test_data_contracts.py      #   train∩test=∅ 用 hash 验
    ├── test_metrics.py             #   已知输入→已知指标值
    └── test_determinism.py         #   同 seed 同 config 两次跑结果一致
```

---

## 3. data 组织规范(既通用又深入)

**核心洞见:把「datasets(字节)」与「tasks(数据+指标+协议+prompt)」分开。** 同一份数据可定义多个任务,而"任务协议"(prompt 模板、答案抽取、指标口径)才是最容易被人偷偷改的地方。

### 3.1 datasets 层(`src/data/` + `data/`)
- `data/registry.yaml`:每个数据集登记 `source_url / license / version / sha256 / contamination_status`。**没有 checksum 的数据禁止进 processed。**
- 分层:`raw/`(只读地基)→ `interim/`(可重建,git 忽略)→ `processed/`(最终形态 + `fingerprint.txt`)。
- 合成数据(模式 D):**"源"是生成脚本 + 生成器模型版本 + seed**,不是产出的 jsonl。产出可从源重建,故产出 git 忽略、源入库。

### 3.2 污染检测是一等公民(`src/data/contamination.py`)
- test 的 n-gram/embedding 是否命中骨干语料或你的训练集。
- 污染状态写进 `DATA_CARD.md`,污染的 benchmark 结论在 report 标红。
- `tests/test_contamination.py`:已知污染样本必须被检出,否则检测器本身失效。

### 3.3 tasks 层(`src/tasks/<benchmark>/`)
把该 benchmark 的 prompt 模板、few-shot 例子、答案抽取正则、指标全部收拢在一处。这样"换了 prompt 导致分数变"这件事在 git diff 里可见、可 review。

---

## 4. 环境规范(可执行 + 可被 gate 校验)

环境是 AI 复现的头号杀手。以下是可执行规范,不是口号。

### 4.1 用 `uv`,不是裸 venv
裸 `venv + pip` 锁不住 CUDA/torch 来源。`uv` 是当前 vLLM 官方推荐路径,`--torch-backend` 自动匹配驱动的 CUDA index。

```bash
# env/setup_env.sh 的核心
uv venv --python 3.12 --seed --managed-python   # vLLM 只支持 3.9–3.12
source .venv/bin/activate
uv pip install vllm --torch-backend=auto          # auto 按 nvidia-smi 驱动选 torch index
```

> **Python 版本铁律**:vLLM 官方要求 3.9–3.12。ContestOS 主控可用 3.14,但**科研子项目运行环境单独锁 3.12**。这正是"每个项目独立锁环境"的意义。

### 4.2 最隐蔽的坑:驱动 CUDA 版本不匹配
vLLM 预编译 wheel 绑定特定 CUDA(如 12.1 / 13.0)。若机器驱动只支持 CUDA 12.x,默认 wheel 会 `import vllm` 成功但 `vllm serve` 崩在 `libcudart.so.13: cannot open shared object file`。

**规范做法**:装前 `nvidia-smi` 读驱动;驱动是 12.x 就显式装匹配的 `+cu129` wheel:
```bash
uv pip install \
  "https://github.com/vllm-project/vllm/releases/download/v0.21.0/vllm-0.21.0+cu129-cp38-abi3-manylinux_2_34_x86_64.whl" \
  --torch-backend=cu129
```
把 `nvidia-smi` 输出 + CUDA 版本抓进 `env/env.lock.json`。
> 注:上面的 wheel URL 是 **Linux x86_64** 场景;macOS 场景无 CUDA wheel,直接用 `uv pip install vllm --torch-backend=auto`,训练/推理到 Linux GPU 机上跑。

### 4.3 三层环境锁 + 一个自检
```
env/
├── setup_env.sh          # 唯一入口
├── pyproject.toml        # [[tool.uv.index]] 固定 pytorch CUDA index(团队/CI 一致)
├── uv.lock               # 精确到 hash 的依赖锁
├── Dockerfile            # 系统层:CUDA/驱动/flash-attn 编译环境
└── verify_env.py         # 装完自检
```
`verify_env.py` 把"环境搭好了"从主观变机器可判:CUDA 可用、vLLM 版本符合 registry 要求、GPU 数满足 tp_size、dtype 一致——任一不满足直接红。这是环境层的 [RUNTIME] gate。

### 4.4 源 / 下载规范
- **依赖源**:pyproject 里 pin torch 的 CUDA index url,不靠"装时正好是哪个源"。国内/内部机器配镜像(HF endpoint / 内部 pypi),但**镜像只影响速度不影响版本**——版本由 `uv.lock` + registry 的 hash 锁死。
- **模型下载**:`registry.yaml`(revision + sha256)+ `download_model.py`。补一条离线复现测试:设 `HF_HUB_OFFLINE=1`,若开离线仍跑通,证明权重真落盘且被 registry 追踪,没偷偷拉 latest。挡"骨干漂移"的 [RUNTIME] 校验。
- **provenance**:每次下载写 `provenance.json`(何时/从哪源/什么 revision/sha256),落到 `models_cache/<model>@<revision>/`,`chmod` 只读,不同版本物理隔离。

### 4.5 其他必须考虑项
- **随机性完整闭环**:不只 `seed`,还有 `torch.use_deterministic_algorithms`、`CUBLAS_WORKSPACE_CONFIG`、vLLM 采样 seed,全进 manifest。
- **chat template 锁定**:同骨干 chat template 变了结果就变。registry pin template(builtin 版本或锁定文件)。LLM 特有、极易忽略的复现漏洞。
- **compute budget 披露**(顶会要求):每个 run 记 GPU 小时 / token 数,进 manifest,report 汇总。
- **CI 只做"小而真"冒烟**:CI 无大 GPU,用最小骨干(0.5B)+ 极小样本跑通 `reproduce.sh` 的流程,证明代码路径不假死;全量复现在自有算力。

---

## 5. 关键文件模板(agent 直接照抄结构)

### 5.1 `models/registry.yaml`(骨干唯一事实源)
```yaml
qwen2.5-7b-instruct:
  hf_repo: Qwen/Qwen2.5-7B-Instruct
  revision: a09a35458c702b33eeacc393d103063234e8bc28   # ★ commit hash,非 tag/latest
  sha256_index: 3f9c...        # 权重清单校验
  quantization: none
  license: apache-2.0
  chat_template: builtin       # 或指向锁定的模板文件路径
  source: huggingface          # / modelscope / 内部镜像
```
`registry.py`:不带 `revision` 的引用直接拒绝加载 → 从源头挡"骨干漂移"。

### 5.2 `experiments/.../manifest.json`(run 身份证)
```json
{
  "run_id": "2026-08-04T14-22_main_qwen2.5-7b_seed0",
  "experiment": "main",
  "git_sha": "9f3c1a2",
  "git_dirty": false,
  "config_hash": "sha256:...",
  "data_fingerprint": "sha256:...",
  "split_hash": "sha256:...",
  "backbone": {"key":"qwen2.5-7b-instruct","revision":"a09a35...","backend":"vllm","vllm_version":"0.x"},
  "sampling": {"temperature":0.0,"top_p":1.0,"seed":0,"max_tokens":2048},
  "serving": {"tp_size":2,"dtype":"bfloat16"},
  "determinism": {"torch_deterministic":true,"cublas_workspace":":4096:8"},
  "task": "gsm8k",
  "contamination_checked": true,
  "method": "your_method@v3",
  "seed": 0,
  "seeds_planned": [0,1,2],
  "compute": {"gpu_hours": 3.2, "total_tokens": 1.4e7},
  "env": {"python":"3.12","cuda":"12.4","gpu":"A100","pip_lock":"sha256:..."},
  "started_at": "...", "finished_at": "...",
  "status": "done",
  "metrics_path": "metrics.json"
}
```
**铁律**:`git_dirty=true` 或 `status!=done` 的 run **不允许**进 `results/`。纯脚本可判,[SCAN]。

### 5.3 `docs/HYPOTHESIS_LEDGER.md`(反灌水账本)
```markdown
## H-007  加 dropout 能否降过拟合
- 假设:val/train gap > 0.15 是过拟合,dropout=0.3 应缩小 gap
- 做法:experiment=ablation_dropout, seeds=[0,1,2]
- 预注册指标:val_acc, train_val_gap（跑之前定死,防事后挑指标）
- 结果:gap 0.18→0.16,val_acc 无显著变化(±std 重叠)
- 结论:❌ 无效,不采纳。run: 2026-08-04T..._ablation_dropout_seed0
```
**"预注册指标"是精髓**:实验前写死看哪个指标,防跑完挑好看的当结论。失败实验必须保留(❌ 也是结果)。

### 5.4 RL recipe 特有落盘(`recipe/rl/`)
```
src/rollout/generator.py   # 用 vLLM 批量生成轨迹
src/reward/                # rule_reward / model_reward(版本 pin)
src/roles/                 # actor/reference/critic 编排(Ray + vLLM + DeepSpeed 协同)
experiments/.../rollouts/  # ★ 每步 rollout + reward 分布 + KL 曲线落盘
```
**RL 硬锚**:reward 曲线 + KL 曲线必须落盘。reward 一路涨但 KL 爆炸 = reward hacking 典型信号 → 变成可见证据,不靠自觉。

---

## 6. 不可造假硬锚 + enforcement 分档

对应总原则:**判据与判真假的东西必须独立于生成者。** 人只在一处介入。

| 硬锚 | 为什么造不了假 | 谁验 |
|---|---|---|
| `reproduce.sh` 在 CI 从零跑出主表(冒烟版) | 环境+数据+seed 全锁,复现不出当场红 | [RUNTIME] |
| 骨干 revision + checksum | 换骨干哈希对不上 | [SCAN] |
| sampling params 全记录 | 复现跑不出你的数当场露 | [SCAN] |
| `split_hash` 断言 train∩test=∅ | 泄漏在哈希层暴露 | [SCAN] |
| 多 seed 的 std | 单点结果无法伪装成稳定提升 | [SCAN] |
| Method 与 baseline 同接口同骨干矩阵 | 不公平对比在骨干列暴露 | [SCAN+REVIEW] |
| baseline 本地复现 ≈ 原论文 | harness 错了连 baseline 都对不上 | [REVIEW] |
| HF/vLLM 一致性容差测试 | serving 混用当场报警 | [RUNTIME] |
| 污染检测 + DATA_CARD 标注 | 虚高分被标红 | [SCAN+RUNTIME] |
| `git_dirty=false` 才进 results | 有脏改动=不可复现,机器判 | [SCAN] |
| HYPOTHESIS_LEDGER 预注册指标 | 事后挑指标与预注册对不上 | [REVIEW] |
| agent trajectory 可回放 + 多seed | 报最好一次无法伪装成稳定 | [SCAN] |
| RL reward/KL 曲线落盘 | reward hacking 在曲线上暴露 | [RUNTIME+REVIEW] |
| `verify_env.py` 自检 | "环境搭好了"从主观变机器可判 | [RUNTIME] |
| `HF_HUB_OFFLINE=1` 离线复现 | 偷偷联网拉 latest 当场失败 | [RUNTIME] |
| **零 fallback 扫描**(§9.2) | 静默降级=造假温床,宁崩不兜底 | [SCAN+REVIEW] |
| 差分测试 naive reference(§9.1) | 复杂实现对不上朴素实现当场露 | [RUNTIME] |
| 效率/质量数出自同一 run(§9.4) | 降级换速无法伪装成又快又准 | [REVIEW] |

**enforcement 分档**:`[AUTO]` formatter/linter,无人;`[SCAN]` gate 脚本(读只);`[REVIEW]` 异构模型(codex 判"真不真");`[RUNTIME]` 真实运行取证;`[HUMAN]` 仅架构/协议决策。

**人的唯一介入点**:`ARCHITECTURE.md` + `EXPERIMENT_PROTOCOL.md` 定稿时拍板(分层、评测协议、骨干矩阵、多 seed 数、污染规则)。之后所有验收由机器/异构模型执行,人不看细节。

---

## 7. agent 落地步骤(scaffold 顺序)

1. 读 `RESEARCH_MODE.md`,确定模式 A/B/C/D → 决定启用哪些 `recipe/` 与 `src/` 子目录(未启用的不建空目录)。
2. 先写 `ARCHITECTURE.md`(4 块:分层 / 依赖图 / 边界 / 被否决方案)→ 这是 [HUMAN] 拍板点,等确认再动代码。
3. 建 `env/`:`setup_env.sh` → `verify_env.py` 跑通(CUDA/vLLM/GPU 自检绿)才继续。
4. 建 `models/registry.yaml` + `download_model.py`,下载骨干并校验 checksum,`HF_HUB_OFFLINE=1` 离线复现测试通过。
5. 建 `src/` 三个抽象接口:`Backbone` / `Method` / `Task`(method 与 baseline 都实现 `Method`)。
6. 建 `conf/`(Hydra 组合)、`scripts/`(薄编排)、`experiments/`(不可覆盖 run 目录 + manifest)。
7. 建 `tests/`:先让 `test_env` / `test_backbone_contract` / `test_contamination` / `test_determinism` 绿。
8. 装 gate:`git_dirty`/`revision`/`split_hash`/`seeds_planned` 的 [SCAN] 脚本 + **`gate_no_fallback.py`(§9.2 零兜底扫描)** + `reproduce.sh` 的 CI 冒烟。
9. 首个实验前在 `HYPOTHESIS_LEDGER` 预注册指标;跑完(含负结果)入账本;`make_report.py` 生成 `results/main_table.md`(骨干列一致、多 seed std)。
10. 交付走 `delivery/UNIT.md` 5 行骨架。

---

## 8. 外部依赖分层治理(引擎 / 框架 / 评测 / 模型 / 数据 / 源)

不能把所有外部东西用一个 registry 一刀切。按"你和它的关系"分 5 层,每层治理动作不同。总判据:**任何会漂移的外部物,都要 pin 死 + 划信任边界 + 记录"复用还是自研"的决策。**

| 层 | 例子 | 关系 | 治理动作 | 绝不做 |
|---|---|---|---|---|
| **L1 运行时引擎** | vLLM、transformers、deepspeed、flash-attn | 用,绝不 fork | `uv.lock` pin;`health_check` + 契约测试;版本进 manifest | 不改源码;不跨版本拼结果 |
| **L2 研究框架** | **verl**、OpenRLHF、TRL | 在它上面搭,继承其正确性和 bug | vendored pin 到 commit;写 adapter 边界 | 不散引用;不 pip 装 latest |
| **L3 评测 harness** | lm-eval-harness、bench | 调用它算分,它的定义会漂 | pin task 版本/commit;包在你的 `Task` 接口后 | **绝不自己重实现指标** |
| **L4 模型** | 骨干、reward model、judge | 冻结的输入 | `models/registry.yaml`:revision + sha256 + chat_template | 不用 `latest`/不带 revision |
| **L5 数据** | benchmark、训练集、合成数据 | 冻结的输入 | `data/registry.yaml`:sha256 + license + 污染状态 | 无 checksum 不进 processed |

### 8.1 L1 · vLLM(用,不碰)
- **版本 pin**:`uv.lock` 锁死 vLLM + torch CUDA index;`env.lock.json` 记录跑时 `vllm.__version__`。
- **契约测试**(`test_backbone_contract.py`):同输入 + 同 seed,vLLM 后端与 HF 后端输出差异在容差内 → 挡"换 vLLM 版本采样行为悄悄变"。
- **每个 run 记 backend**:manifest 写清这批数是 vLLM 还是 HF 出的;**禁止跨 backend 拼一张表**。
- **不 fork**:要改行为走它暴露的参数(logits_processor、sampling params),不改源码。

### 8.2 L2 · verl(项目默认:直接复用,不自研 RL)
**决策已定并写入本规范**:RL 训练**默认直接用 verl**——它对四角色编排 / Ray 调度 / vLLM rollout 集成的实现已经足够好,自研 RL 极易在 advantage/KL/mask 上写错(RL 最难调对的地方),ROI 不划算。

治理动作:
- **vendored + pin 到 commit hash**(不是 `pip install verl`,latest 会漂);verl 的 commit 记进 `env.lock.json`。
- 你的贡献通过 `recipe/rl/` 挂进 verl 的扩展点,写一层 **adapter** 划清边界:哪些是 verl 的、哪些是你的,reviewer 一眼可分。
- **不改 verl 核心**;确需改,fork 单独提 PR 级说明,进 `DECISIONS.md`。
- 例外(需在 `DECISIONS.md` 显式论证才允许自研):verl 不支持你要的算法/结构,且改扩展点也做不到。

### 8.3 L3 · 评测 harness(复用,绝不重实现指标)
- **最危险反模式**:自己手写 gsm8k/MMLU 的答案抽取+算分 → 分数与他人不可比,抽取正则写歪几个点没人知道。
- **规范**:调标准 harness(lm-eval task 以 yaml 组织,数据+指标+协议收拢),pin 到 task commit,再包在你的 `Task` 接口后。`tasks/<benchmark>/` 只做"骨干接入 + prompt 模板锁定",算分委托 harness。
- **例外**:harness 没有的新 benchmark 才自实现,且必须配 `test_task_contract.py`(已知样例→已知分)使其可回归。

### 8.4 baseline(横切:本地复现 + 容差)
- 铁律:baseline 走**同一 harness、同一骨干矩阵**本地跑出,禁止"引自某论文"的不可复现数字。
- `baselines/REPRO_REPORT.md`:证明本地复现分 ≈ 原论文(声明容差如 ±0.5)。**本质是验证你 harness 本身对不对**——连别人 baseline 都复现不到原值,自己的数不可信。[REVIEW]。

### 8.5 源(横切:版本由 hash 锁,源只管速度)
- 依赖源:`pyproject.toml` 的 `[[tool.uv.index]]` pin torch 的 CUDA index url。
- 模型源:registry 的 `source: huggingface / modelscope / 内部镜像`;**镜像只影响下载速度,不影响版本**——版本由 revision + sha256 锁死;`HF_HUB_OFFLINE=1` 离线复现证明没偷偷拉新的。

---

## 9. 代码的正确性 / 质量 / 效率(架构管不到的那一层)

架构定"放哪",本章定"放进去的对不对、干不干净、快不快"。三者机制不同,分开保证。总原则不变:**判真假的东西必须独立于生成者**——下面每个手段都是一个独立于"写代码那个 agent"的裁判。

### 9.1 正确性:靠独立 oracle,不靠"跑通"

跑通 ≠ 正确。loss 在降也不代表实现和 method 意图一致。5 个独立裁判(便宜→贵):

1. **差分测试 / naive reference**(头号武器):任何为快而写的复杂实现(融合 kernel、向量化、缓存),都配一个**慢而显然对**的朴素实现,断言两者容差内一致。naive 版太简单以至不可能写错,就是"独立于生成者的判据"。[RUNTIME]
   ```python
   def test_fast_matches_naive():
       x = torch.randn(2, 8, 16)
       assert torch.allclose(my_fused(x), naive_loop(x), atol=1e-4)
   ```
2. **已知答案(analytic oracle)**:有解析解的部件用手算断言。如 KL(p‖p)=0、softmax 和为 1、reward 在构造样例的确切值、DPO loss 在 margin=0 的值。
3. **梯度检查**:自定义 backward 用 `torch.autograd.gradcheck`(数值 vs 解析)。RL/自定义 loss 最易在此露馅。
4. **过拟合单 batch**(catch 90% bug):1 个 batch 反复训,loss 必须压到近 0;压不下去 = 数据/loss/mask/lr 有 bug。是训练类最便宜的正确性冒烟 [[A Recipe for Training Neural Networks]](https://karpathy.github.io/2019/04/25/recipe/)。
5. **端到端复现 baseline**(集成级):复现出原论文数,证明整条 harness 对。最贵但最有说服力。

RL/agent 额外硬锚:**reward↑ 同时 KL 是否失控**(reward hacking 指纹)、**agent 轨迹可回放**(同 seed 同路径)。曲线落盘 = 正确性证据可审计。

### 9.2 【铁律】零 fallback / 零静默降级——宁可失败,不许兜底

> **这是本项目最强的一条正确性规范,优先级高于"能跑"。** 科研代码里静默降级 = 数据造假的温床:一个 except 吞掉,结果就是错的还不知道。**要么正确运行,要么当场崩溃,绝不允许"降级后继续跑出一个看起来正常的数"。**

**禁止清单(出现即 gate 失败):**
- 禁 `try/except` 兜底:除非 except 分支**立即 `raise`**(重抛/包装错误上下文),否则禁止。绝不允许 `except: pass`、`except: return None/0/[]/默认值`、`except: 走另一条路`。
- 禁 `else` 降级:禁止"首选路径失败/不可用 → else 走一条更差的路"(如 GPU 不可用就转 CPU、vLLM 起不来就转 HF、加载失败就用随机初始化)。这些情况**直接报错退出**。
- 禁静默默认值:配置缺失、文件缺失、key 不存在 → 报错,不许 `.get(k, default)` 静默填默认。
- 禁能力探测式回退:`if has_flash_attn: ... else: 普通attention` 这类"有就用没就退"——要用什么在 `conf/` 里显式声明,环境不满足由 `verify_env.py` **提前**报错,而不是运行时悄悄退。

**允许的例外(唯一):** 面向**外部不可控**的重试(网络下载、API 限流),且必须:①有次数上限;②耗尽后 `raise`;③重试事件写日志。这不是降级,是"最终仍会失败"的有限重试。

**enforcement**:
- [SCAN] `gate_no_fallback.py` 正则扫 `git diff`:`except\s*:`、`except[^:]*:\s*(pass|return|continue)`、`\.get\([^,]+,\s*[^)]+\)` 可疑默认、`is_available\(\)` 后接 else 分支 → 命中即红(白名单标注 `# noqa: fallback-reviewed` 且需 REVIEW 通过)。
- [REVIEW] 异构模型专答一问:"这段代码里有没有任何路径,在出错/资源不满足时不报错而是继续产出一个结果?" 有 → DEGRADED。

### 9.3 质量(干净度):src 生产标准,notebooks 豁免

分区:探索区(notebooks)允许乱,固化进 `src/` 就按大厂标准(要被复现/review/复用)。

| 项 | 规则 | 档 |
|---|---|---|
| 格式化 / lint | ruff + 格式化 | [AUTO] |
| 依赖单向 | import-linter:`eval` 不 import `train`;`src` 不 import `notebooks`;`method` 不 import 具体 backbone | [SCAN] |
| 复杂度 | 圈复杂度 ≤10,函数 ≤60 行,文件 ≤600 行 | [AUTO] |
| 边界类型 | Backbone/Method/Task 三接口必须类型标注 + docstring 契约 | [SCAN] |
| 死代码 | 无未引用函数 / 注释掉的旧实现 | [AUTO] |
| 无魔法数字 | 超参进 `conf/`,代码禁硬编码 | [SCAN] |
| 完整性诚实性 | 见 §9.2 零 fallback 铁律 | [SCAN+REVIEW] |

### 9.4 效率:vLLM 吃满卡即达标,不做无谓雕花

**项目效率哲学(已定)**:效率的达标线 = **用 vLLM 把 GPU 充分利用**。除非满足以下触发条件,否则不追加优化,避免性能雕花浪费时间:
- **触发继续优化的条件**:①瓶颈明确在 CPU(GPU 长期打不满且 profile 证明卡在 CPU/数据侧);②存在明显的可缓存 / 可复用中间结果(如重复的 prompt 编码、可复用的 KV、可复用的特征);③存在明显的可预处理项(如 tokenize/特征提取可离线一次性做完)。

**规范**:
1. **效率是被记录的指标,不是感觉**:manifest 记 `throughput(tokens/s)`、`GPU util`、`gpu_hours`。GPU util 长期偏低 → 触发上面的排查,而非默默忍受。
2. **禁"降级换速度"**(呼应 §9.2):吞吐数字必须来自**产出质量数字的同一个 run**。禁止测速用短序列、测分用长序列拼一张表。[REVIEW] 判"这俩数是不是同一次跑的"。
3. **profile 而非猜**:确定要优化时,先 `torch.profiler` 定位瓶颈,profile 摘要存进 `experiments/.../` 作为"确实测过瓶颈在哪"的证据,再动手。禁止凭直觉改。
4. **不过早优化**:vLLM 已吃满卡时,不为微小收益重写复杂逻辑——复杂度换来的可读性/正确性损失通常不值。

---

## 附:引用的真实实现佐证
- verl(顶层 `recipe/` 承载不同算法配方,共用 `verl/` 包):https://github.com/volcengine/verl
- OpenRLHF(SFT/DPO/PPO/RM 一套 CLI 切换;Actor/Reward/Reference/Critic 分 GPU,Ray+vLLM+DeepSpeed):https://github.com/OpenLLMAI/OpenRLHF
- lm-evaluation-harness(task 以 yaml 组织,数据+指标+协议收拢):https://github.com/EleutherAI/lm-evaluation-harness
- vLLM + uv 环境规范(`--torch-backend`、CUDA 匹配、`+cu129` wheel):https://pydevtools.com/handbook/how-to/how-to-use-vllm-with-uv/
- vLLM GPU 安装要求(Python 3.9–3.12、CUDA 版本):https://docs.vllm.ai/en/v0.7.0/getting_started/installation/gpu/index.html
- A Recipe for Training Neural Networks(过拟合单 batch 等健全性检查):https://karpathy.github.io/2019/04/25/recipe/
