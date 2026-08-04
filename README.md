# agent-sop

个人 agent 开发规范体系仓库。三个平行概念,组成完整的地基:

## 三个概念

| 概念 | 位置 | 一句话 | 回答的问题 |
|---|---|---|---|
| **纪律(Principles)** | [PRINCIPLES.md](PRINCIPLES.md) | 四条核心纪律(P1 契约先行 / P2 独立 oracle / P3 零 fallback / P4 可追溯)+ 收纳判据 | **为什么**这么做 |
| **骨架(Skeletons)** | [skeletons/](skeletons/README.md) | 一个**项目**的完整结构标准(目录树 + 防腐职责 + 硬锚) | **项目长什么样** |
| **SOP(可组合规程)** | [sop/](sop/README.md) | 一段可复用的、agent 可执行的规程,三层组织、可互相调用 | **怎么做一件事** |

> 纪律是"为什么",骨架是"项目长什么样",SOP 是"怎么做一件事"。

## 结构

```
agent-sop/
├── PRINCIPLES.md          # 四条核心纪律 + 收纳判据(全仓地基)
├── skeletons/             # 项目骨架(3 份:科研/竞赛/开发,内容零改动)
│   └── README.md          # 骨架索引
├── sop/                   # 可组合规程库(三层)
│   ├── README.md          # 三层 INDEX + 依赖图 + 纪律映射
│   ├── _TEMPLATE.md       # 单条 SOP 统一模板
│   ├── tier0-core/        # 核心横切(全场景共用,7 条)
│   ├── tier1-skeleton/    # 骨架绑定(8 条)
│   └── tier2-activity/    # 非项目型工作:运维/写作/调研(6 条)
├── templates/             # 模板仓库索引(按需配套)
└── README.md              # 本文件
```

## 使用流程

1. **判断任务是不是"项目"**(有 src/、跨时间存在、有交付物):
   - **是** → 选骨架([skeletons/README.md](skeletons/README.md)),在项目 CLAUDE.md 引用相关 tier0/tier1 SOP。
   - **不是**(运维/写作/调研)→ 直接走 [sop/tier2-activity/](sop/README.md) 的活动型 SOP。
2. **所有情况都受 PRINCIPLES 约束**(任何 skeleton/SOP 必须落实至少一条纪律)。
3. 需要项目骨架直接开工 → clone [contestos-starter](https://github.com/VikingDeng/contestos-starter)。

## 新增一个 SOP

1. 用 [sop/_TEMPLATE.md](sop/_TEMPLATE.md) 建文件,放到对应层级目录(`tier0-core` / `tier1-skeleton` / `tier2-activity`)。
2. 头部填"落实纪律"(必须映射到 PRINCIPLES 的某条,对不上则先补纪律)。
3. 更新 [sop/README.md](sop/README.md) 索引。

## 新增一个骨架

1. 文档放 `skeletons/<语义名>-v<版本>.md`,头部声明落实的纪律。
2. 更新 [skeletons/README.md](skeletons/README.md) 索引。
3. 需要模板骨架 → 建模板仓库(标记 Template Repository)→ 登记到 [templates/README.md](templates/README.md)。
