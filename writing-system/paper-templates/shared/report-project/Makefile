# ------------------------------------------------------------
#  分层文档工程构建入口（由 paper-templates 脚手架生成，随工程一起拷走）
#
#  标准构建依赖三件：Python 3（build/watch 先校验 template.lock）、typst、GNU make。
#  模板源码固定在 vendor/template/ 快照里，
#  不联网、不装包、不需要 @local / @preview。
#
#    make build     编译到 build/main.pdf（phony：每次真的重新编译）
#    make watch     存盘即编译
#    make verify    校验 vendor/ 快照 sha256（build/watch 前自动执行）
#    make lockcheck verify 的别名，两个名字等价
#    make lock      升级模板后显式重写 template.lock（构建永不自动跑）
#    make clean     只删本工程已知构建产物，保留 build/ 下其它文件
#    make version   打印引擎版本
#
#  产物默认 build/main.pdf。要换位置用
#    make build OUT='output custom/main.pdf'
#  父目录会自动创建，路径带空格也可以；改到别处的产物不要提交。
#  Python 解释器默认探测 python3，再退到 python；可用 make PYTHON=... 覆盖。
#
#  没有 GNU make 的 Windows：README.md 第一节给了等价的 PowerShell 命令。
# ------------------------------------------------------------
TYPST  ?= typst
PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
MAIN   := main.typ
BUILD  := build
OUT    := $(BUILD)/main.pdf
FLAGS  ?=
LOCKV  := tools/verify_template_lock.py

.PHONY: all build watch verify lockcheck lock clean version help _check-python

all: build

## 编译产物；默认 build/main.pdf，用 OUT=... 指定别处（父目录自动创建）
build: verify
	@mkdir -p "$$(dirname -- "$(OUT)")"
	$(TYPST) compile $(FLAGS) $(MAIN) "$(OUT)"
	@echo "built $(OUT)"

## 存盘即编译（同样先校验 lock）
watch: verify
	@mkdir -p "$$(dirname -- "$(OUT)")"
	$(TYPST) watch $(FLAGS) $(MAIN) "$(OUT)"

## 校验 template.lock 与 vendor/template/ 的 sha256 是否一致（只读，不改 lock）
verify: _check-python
	@$(PYTHON) "$(LOCKV)"

## verify 的别名；旧脚本里两个名字都出现过，保留兼容
lockcheck: verify

## 升级 vendor/template/ 后手动重写 lock；build/watch 不会自动调用它
lock: _check-python
	$(PYTHON) "$(LOCKV)" --write

## 内部：Python 3 必须存在且真的是 Python 3，否则明确失败（不自动安装）
_check-python:
	@if [ -z "$(PYTHON)" ]; then \
		echo "错误：找不到 Python 3（python3 或 python）。"; \
		echo "      build/watch/verify 需要它校验 template.lock；本工程不会自动安装依赖。"; \
		echo "      装好 Python 3 后重跑，或 make PYTHON=/path/to/python3 ..."; \
		exit 1; \
	fi
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' \
		|| { echo "错误：$(PYTHON) 不是可用的 Python 3。"; exit 1; }

## 只删已知产物 $(OUT)；build/ 下的其它文件（如 user-note.txt）保留
clean:
	rm -f "$(OUT)"
	@rmdir "$(BUILD)" 2>/dev/null || true

version:
	@$(TYPST) --version

help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  /'
