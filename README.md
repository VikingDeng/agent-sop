# agent-sop

一个人主导、多个 agent 会话协作时用的最小执行规范。人负责意图、验收、关键代码和排错假设，agent 负责扩大产出和找证据。每过一个关卡就复盘一次，把教训改进规则里，或者把不再有用的规则删掉。

## 用法

1. 每个实质任务先读 [KERNEL.md](KERNEL.md)，只有一页。
2. 再按任务类型加载一份 playbook：
   - 给上游 LLM infra 项目（verl、Megatron-LM 等）提 PR：[playbooks/oss-pr.md](playbooks/oss-pr.md)
   - 实现已批准的研究 proposal 并跑实验：[playbooks/research.md](playbooks/research.md)
3. 过了一个关卡（PR 合并或关闭、实验得出结论、一次明显返工）后，按 [retro/TEMPLATE.md](retro/TEMPLATE.md) 写复盘，放在 `retro/` 下。

中文技术写作，包括论文、报告和 PR 描述，使用 [writing-system/](writing-system/README.md)。它是只读快照，改动规则见 [AGENTS.md](AGENTS.md)。

## 目录

```text
KERNEL.md        所有任务通用的规则
playbooks/       按任务类型补充的证据要求
retro/           复盘模板和复盘记录
writing-system/  写作体系 v1.0 只读快照
scripts/check_docs.py  链接与篇幅检查（CI 会跑）
```

## 历史

精简前的完整仓库（三层 SOP、Skill 治理、开放质量评测、ContestOS skeleton 等）保存在标签 `archive/pre-slim-2026-10`；需要某个文件时可以恢复：

```sh
git checkout archive/pre-slim-2026-10 -- <path>
```

Codex 运行时适配层（Sol/Terra/Luna 路由、Hook、安装器）在 `codex-adapter` 分支上单独维护。
