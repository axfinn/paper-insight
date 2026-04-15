#!/bin/bash
# Paper Insight 统一运行脚本
# 用法: ./run.sh <命令>

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    echo """
╔══════════════════════════════════════════════════════════════╗
║              Paper Insight 统一入口                         ║
╠══════════════════════════════════════════════════════════════╣
║  ./run.sh build     构建 Docker 镜像                         ║
║  ./run.sh start     启动服务                                 ║
║  ./run.sh stop      停止服务                                 ║
║  ./run.sh restart   重启服务                                 ║
║  ./run.sh logs      查看日志                                 ║
║  ./run.sh status    查看状态                                 ║
║  ./run.sh deploy    一键部署（构建 + 启动）                   ║
╚══════════════════════════════════════════════════════════════╝
"""
}

# 创建必要目录
init_dirs() {
    mkdir -p papers reports github logs data autodev_workspace hugo_site/public
}

# 构建
do_build() {
    echo "[*] 构建 Docker 镜像..."
    docker compose build --no-cache
}

# 启动
do_start() {
    init_dirs
    echo "[*] 启动 Paper Insight..."
    docker compose up -d
    sleep 3
    echo "[✓] 启动完成"
    echo ""
    echo "🌐 访问主页: http://localhost:8084"
    echo "📊 状态监控: http://localhost:8084/status"
}

# 停止
do_stop() {
    echo "[*] 停止 Paper Insight..."
    docker compose down
    echo "[✓] 已停止"
}

# 重启
do_restart() {
    do_stop
    sleep 1
    do_start
}

# 日志
do_logs() {
    shift
    docker compose logs -f "$@"
}

# 状态
do_status() {
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q paper-insight; then
        echo "[✓] 容器运行中"
        docker compose ps
        echo ""
        echo "🌐 访问主页: http://localhost:8084"
        echo "📊 状态监控: http://localhost:8084/status"
    else
        echo "[✗] 容器未运行"
        echo "   使用 ./run.sh start 启动"
    fi
}

# 一键部署
do_deploy() {
    init_dirs
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        echo "[!] .env 已创建，请编辑填入 ANTHROPIC_AUTH_TOKEN"
        echo "[*] 启动跳过，请先配置 .env"
        return 1
    fi
    echo "[*] 一键部署..."
    docker compose down
    docker compose up -d --build
    sleep 3
    echo ""
    echo "[✓] 部署完成"
    echo ""
    echo "🌐 访问主页: http://localhost:8084"
    echo "📊 状态监控: http://localhost:8084/status"
    docker compose logs --tail=20
}

case "${1:-help}" in
    build)  do_build ;;
    start)  do_start ;;
    stop)   do_stop ;;
    restart) do_restart ;;
    logs)   do_logs "$@" ;;
    status) do_status ;;
    deploy) do_deploy ;;
    *)      show_help ;;
esac
