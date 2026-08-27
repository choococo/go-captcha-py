.PHONY: dev dev-vue dev-react dev-svelte dev-solid dev-js dev-angular backend test lint format precommit build samples e2e help

# 一键前后端（Ctrl-C 一起停）
dev:            ## 后端 + Vue demo（默认）
	./dev.sh vue
dev-vue:        ## 后端 + Vue demo
	./dev.sh vue
dev-react:      ## 后端 + React demo
	./dev.sh react
dev-svelte:     ## 后端 + Svelte demo
	./dev.sh svelte
dev-solid:      ## 后端 + Solid demo
	./dev.sh solid
dev-js:         ## 后端 + 原生 JS demo
	./dev.sh js
dev-angular:    ## 后端 + Angular demo
	./dev.sh angular
backend:        ## 仅后端 (:9000, Swagger: /docs)
	./dev.sh backend

# 质量与构建
test:           ## 跑全部测试
	uv run --extra fastapi pytest tests/ -q
lint:           ## ruff 检查
	uv run ruff check src tests examples
format:         ## ruff 格式化
	uv run ruff format src tests examples
precommit:      ## pre-commit 全钩子
	uv run pre-commit run --all-files
build:          ## 构建 wheel + sdist
	uv build
samples:        ## 生成样例图到 captcha-output/
	uv run go-captcha-py captcha-output

# Vue demo 浏览器自动化（需后端 GOCAPTCHA_DEBUG=1 已起）
e2e:            ## Playwright 无头解四种验证码（后端需以 debug 模式先起）
	cd examples/vue-demo && node e2e-solve.js

help:           ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
