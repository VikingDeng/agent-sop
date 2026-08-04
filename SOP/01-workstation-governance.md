# SOP 01 — 工作站治理

## 目录约定

| 路径 | 用途 |
|---|---|
| `~/ops` | 工作站自动化与全局 Claude 运行时内容的**事实源**(可编辑) |
| `~/.claude` | 运行时输出(settings、缓存、memory);不作为编辑源 |
| `~/code` | 项目 |
| `~/runs` | worktree 运行 |
| `~/notes` | 笔记 |
| `~/papers` | 文献资产 |
| `WorkSSD` | 大型缓存、数据集、模型、长生命周期上下文 |

## 规则

1. **事实源唯一**:工作站配置以 `~/ops` 为准;`~/.claude` 只读运行时产物。
2. **可重建性**:工作站变更保持脚本化、可重建,沉淀在 `~/ops` 下。
3. **安全边界**:
   - 不把真实密钥、token、cookie、密码写进仓库、笔记、prompt 或共享模板。
   - 高风险的认证制品(爬虫 cookie、X/Twitter 凭据)与通用运行时配置隔离。
   - X/Twitter 采集作为独立治理路径处理。
4. **项目规则下沉**:优先 repo-local 的 `CLAUDE.md`、任务文件与规则,避免膨胀全局文件。
5. **全局规则只放稳定约束**:跨项目通用、长期稳定的规则才进全局 `CLAUDE.md` / `rules/`。

## 规则文件组织

- `rules/` 用于按路径生效的细化策略(如 `coding.md`、`research.md`、`quality-gates.md`、`hamming-filter.md`、`karpathy-verification.md`)。
- 避免在多个地方重复长指令;一处定义,其余引用。
