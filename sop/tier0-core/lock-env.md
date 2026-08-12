# SOP-lock-env: 锁定与记录可复现环境

- **层级**: tier0-core
- **落实纪律**: P2(环境证据匹配 claim) P3(漂移与不确定性诚实) P4(关键环境可追溯)
- **绑定骨架**: 无
- **通用性档位**: U1（环境机制通用；锁定器、载体与重建命令由项目注入）
- **版本**: v2

## 触发条件

- 新增或升级会影响运行结果的依赖；
- 环境差异可能改变当前 build、runtime、科学结果、发布兼容或复现 claim；
- 需要把一次执行变成可重建的正式证据、发布工件或跨机器 handoff。

普通文本修改、与环境无关的静态检查，以及只需记录现有运行时身份的低风险诊断，不因为本 SOP 存在就强制创建环境文件或重建环境。

## 前置条件

- 已识别当前 claim 与可能改变它的环境表面，例如语言/runtime、直接或传递依赖、系统库、OS/架构、加速后端、驱动或外部服务版本；
- 已检查项目现有的 lockfile、容器、环境管理器、CI 配置、run metadata 或其他可复用载体；
- 能区分“记录本次实际环境”与“证明他人可从零重建同一环境”。前者不自动要求后者。

## 依赖 SOP

无。

## 步骤

1. **从 claim 反推环境边界。** 只锁定或记录能够改变当前结果、兼容承诺或失败语义的环境表面。不要因为工具能导出更多信息，就把全部系统包、硬件细节或全局配置加入关键路径。
2. **优先复用项目原生身份。** 使用项目已有的 `{LOCK_FILE}`、容器 digest、环境文件、包管理器 resolved graph、CI image 或 run manifest。依赖声明允许生态正常使用版本范围；决定性证据需要的是本次实际解析结果可识别、未来重建不会静默漂移，而不是机械禁止所有 range。源码、模型或非 registry 依赖在与 claim 相关时记录 commit、版本或内容身份。
3. **按证据强度补足缺口。** 普通诊断可把实际 runtime/关键依赖版本写入现有日志或 run record；正式科研、发布、跨机器 handoff 或环境敏感结果应具有可重建的依赖与关键平台身份。只有项目现有载体不足、且新增检查能防止具体漂移时，才创建独立 `{ENV_LOCK}` 或 `{VERIFY_ENV}`；二者不是默认产物。
4. **选择最便宜的有效校验。** 可使用 frozen/install 模式、已有 CI、容器 digest、版本探针、import/smoke、ABI 检查或项目原生 environment check。环境完全相等不是通用目标；检查应验证与 claim 有因果关系的兼容或重建条件。
5. **只在需要时做独立重建。** 当发布/confirmatory evidence 的 claim 明确要求可重建，或任务涉及跨机器复现、环境迁移、可信“当前环境偶然可用”失败路径时，在 disposable/独立环境按记录重建并运行匹配 Oracle。普通 exploratory、diagnostic 与 code-readiness 工作不固定要求 clean rebuild。
6. **保存实际执行身份。** evidence-bearing run 记录实际使用的代码、数据、配置、resolved dependencies 与相关 host/device/backend 身份。Git 工作树可以有改动；优先保存 content-addressed snapshot/archive。若用 base commit + delta，delta 必须覆盖 staged、unstaged、execution-relevant untracked、submodule/LFS 与运行时读取的仓库外代码身份，并在重建后对拍 execution-relevant content-tree hash；仅保存普通 `git diff` 不足以证明可恢复。`git_dirty=false` 不是环境正确性的替代证据。

## 门禁

- `[BLOCK]` 环境身份或解析漂移足以改变当前正式 claim、发布兼容或重建结果，却无法识别本次实际执行环境；
- `[BLOCK]` 声称已独立重建/跨机器复现，但实际复用了会掩盖目标失败路径的环境、缓存或中间产物；
- `[SIGNAL]` 低风险诊断缺少非关键环境细节时，只限制其可声称范围，不阻断与该细节无关的安全工作；
- `[HUMAN]` 新凭据、受控镜像/数据、系统级修改、共享环境覆盖或 material/unbounded 资源仍由 Supervisor 决定。

`{LOCK_FILE}`、`{ENV_LOCK}`、`{VERIFY_ENV}`、clean rebuild、容器和 clean Git 都不是所有任务的固定门禁。

## 完成判定

- 与当前 claim 有因果关系的环境表面和本次实际 identity 可复核；
- 所需强度是“可运行”“可重建”还是“独立环境已复现”已明确，没有用较弱证据冒充较强 claim；
- 若当前结果要求可重建或独立复现，相应原生载体、重建命令和匹配 Oracle 已真实通过；
- 未锁定、不可取得或平台相关的边界被准确披露，而不是静默使用浮动替代。

## 失败处理

环境不匹配时保留原错误并判断它是否影响当前 claim。可以在同一结果契约内显式修复依赖、创建新的环境 identity 并重新验收；不得让 evidence-bearing run 自动切换 backend、device、host、依赖集或旧缓存后继续产出成功。若某依赖无法完全 pin，但本次 resolved identity 可保存，则按真实可重建边界交付；只有该缺口会否定当前 claim 时才阻断它，不把所有诊断一并判失败。

## 产物

优先复用项目已有 lockfile、容器/CI 配置和 run metadata。按当前 claim 只补充必要的 resolved identity、重建/校验入口和通过证据；独立 `{ENV_LOCK}`、`{VERIFY_ENV}`、clean-build 报告或跨机器记录均为条件产物，不创建空壳。
