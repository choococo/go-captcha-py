#!/usr/bin/env bash
# go-captcha-py 一键启动：后端 FastAPI + 前端 demo 同时运行
#
# 用法:
#   ./dev.sh              # 后端 + Vue 2 demo（默认）
#   ./dev.sh vue          # 同上
#   ./dev.sh react        # 后端 + React demo
#   ./dev.sh svelte       # 后端 + Svelte demo
#   ./dev.sh solid        # 后端 + Solid demo
#   ./dev.sh js           # 后端 + 原生 JS demo
#   ./dev.sh angular      # 后端 + Angular demo（需要 node>=20，自动用 nvm 的 v22）
#   ./dev.sh backend      # 只起后端
#
# 退出: Ctrl-C 一次性停掉前后端

set -euo pipefail
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-9000}"
LOG_DIR="/tmp/gocaptcha-py-logs"
mkdir -p "$LOG_DIR"

FRAMEWORK="${1:-vue}"

# ---- 前端定义: 描述|目录|启动命令|URL ----
case "$FRAMEWORK" in
  vue)     DESC="Vue 2";        DIR="examples/vue-demo";                              CMD="npm run dev";                    URL="http://localhost:5173" ;;
  react)   DESC="React";        DIR="examples/multi-framework/react-demo";            CMD="npm run dev";                    URL="http://localhost:5174" ;;
  svelte)  DESC="Svelte";       DIR="examples/multi-framework/svelte-demo";           CMD="npm run dev";                    URL="http://localhost:5181" ;;
  solid)   DESC="Solid";        DIR="examples/multi-framework/solid-demo";            CMD="npm run dev";                    URL="http://localhost:5182" ;;
  js)      DESC="原生 JavaScript"; DIR="examples/multi-framework/js-demo";            CMD="npm run dev";                    URL="http://localhost:5183" ;;
  angular) DESC="Angular";      DIR="examples/multi-framework/angular-demo/angular-app"; CMD="npx ng serve --port 4200";     URL="http://localhost:4200" ;;
  backend) DESC="";             DIR="";                                               CMD="";                               URL="" ;;
  *) echo "未知前端: $FRAMEWORK (可选: vue|react|svelte|solid|js|angular|backend)"; exit 1 ;;
esac

PIDS=()

cleanup() {
  echo ""
  echo "🛑 停止所有服务…"
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  echo "bye"
}
trap cleanup EXIT INT TERM

# ---- 后端 ----
echo "🐍 启动 FastAPI 后端 :${BACKEND_PORT}"
# GOCAPTCHA_DEBUG=1 会把答案带在生成接口响应里（仅用于自动化 E2E，本地去验证可开）
uv run --extra fastapi uvicorn examples.fastapi_server:app --port "$BACKEND_PORT" --reload \
  > "$LOG_DIR/backend.log" 2>&1 &
PIDS+=($!)

# 等后端就绪
for i in $(seq 1 30); do
  if curl -s -o /dev/null "http://127.0.0.1:${BACKEND_PORT}/captcha/click"; then
    echo "✅ 后端就绪: http://127.0.0.1:${BACKEND_PORT} (Swagger 文档: /docs)"
    break
  fi
  sleep 0.5
done

if [ "$FRAMEWORK" = "backend" ]; then
  echo "仅后端模式。日志: tail -f $LOG_DIR/backend.log"
  echo "按 Ctrl-C 退出"
  wait "${PIDS[0]}"
  exit 0
fi

# ---- 前端 ----
echo "🚀 启动 ${DESC} demo"
(
  cd "$DIR"
  if [ ! -d node_modules ]; then
    echo "📦 首次运行，安装依赖…"
    npm install
  fi
  # angular 需要 node>=20：本机 nvm 有 v22 时自动切换
  if [ "$FRAMEWORK" = "angular" ] && [ -d "$HOME/.nvm/versions/node/v22.22.0" ]; then
    export PATH="$HOME/.nvm/versions/node/v22.22.0/bin:$PATH"
  fi
  eval "$CMD"
) > "$LOG_DIR/frontend.log" 2>&1 &
PIDS+=($!)

echo ""
echo "═══════════════════════════════════════════════"
echo "  前端: $URL"
echo "  后端: http://127.0.0.1:${BACKEND_PORT}"
echo "  日志: $LOG_DIR/{backend,frontend}.log"
echo "  退出: Ctrl-C"
echo "═══════════════════════════════════════════════"
echo ""
echo "浏览器打开 → $URL"
echo "(如果页面空白: 稍等 vite 首次编译; 看日志: tail -f $LOG_DIR/frontend.log)"

wait
