# SOP-lock-env: 锁定可复现环境

- **层级**: tier0-core
- **落实纪律**: P4(可追溯:环境可回溯、可复现)
- **绑定骨架**: 无(几乎所有 SOP 的隐式前置)
- **通用性档位**: U1(假设存在锁定器,不绑具体工具/语言)
- **版本**: v1

## 触发条件

项目初始化、引入/升级依赖后、或任何"要保证他人/未来能复现同一环境"的时刻。

## 前置条件

- 项目已声明其技术生态与锁定工具 `{LOCK_CMD}` / 锁文件路径 `{LOCK_FILE}`(如 Python+uv → `uv lock` / `uv.lock`;Node → `npm ci` / `package-lock.json`;容器 → 固定 base image digest);
- 依赖清单(声明式)已存在。

## 依赖 SOP

无(基础能力,被几乎所有 SOP 依赖)。

## 步骤

1. 用 `{LOCK_CMD}` 生成/刷新锁文件 `{LOCK_FILE}`,将全部直接与传递依赖固定到精确版本(含哈希,若生态支持)。
2. 记录环境事实到 `{ENV_LOCK}`(如 `env.lock.json`):解释器/运行时版本、关键系统库、加速后端(如 CUDA/torch backend)、OS/架构。
3. 提供一键校验入口 `{VERIFY_ENV}`(如 `verify_env.py`):读取 `{ENV_LOCK}` 并断言当前环境与之一致,不一致即 raise。
4. 把 `{LOCK_FILE}` / `{ENV_LOCK}` 纳入版本控制,与代码同 commit(P4:环境改动可追溯)。
5. 校验复现性:在干净环境按锁文件重建,跑 `{VERIFY_ENV}` 通过。

## 门禁

[AUTO] `{LOCK_FILE}` 存在且非空;`{VERIFY_ENV}` 退出码 0。
[SCAN] 依赖声明中无浮动版本符(如 `*` / `latest` / 无上界范围)进入锁定项。

## 完成判定

- `{LOCK_FILE}` 与 `{ENV_LOCK}` 存在且入库;
- 干净环境按其重建后 `{VERIFY_ENV}` 通过(二值)。

## 失败处理

遵守 P3:若某依赖无法锁定精确版本(源不提供哈希/版本)→ 显式报告该依赖为不可复现风险点,不得"就用浮动版本先跑起来";若 `{VERIFY_ENV}` 检出环境不一致 → raise 并中止后续步骤,绝不"环境对不上但看起来能跑就继续"。

## 产物

锁文件 `{LOCK_FILE}` + 环境事实 `{ENV_LOCK}` + 校验入口 `{VERIFY_ENV}`,三者入库同 commit。
