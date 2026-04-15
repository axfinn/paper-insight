#!/bin/bash
# Paper Insight 统一运行脚本
# 用法: ./run.sh [start|stop|restart|status|logs]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

show_help() {
    echo """
╔══════════════════════════════════════════════════════════════╗
║              Paper Insight 运行脚本                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  用法: ./run.sh <命令>                                        ║
║                                                              ║
║  命令:                                                       ║
║    start     启动服务                                        ║
║    stop      停止服务                                        ║
║    restart   重启服务                                        ║
║    status    查看状态                                        ║
║    logs      查看日志                                        ║
║    deploy    一键部署（重新构建）                             ║
║                                                              ║
║  示例:                                                       ║
║    ./run.sh start                                            ║
║    ./run.sh logs -f                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
}

start() {
    echo "[*] 启动 Paper Insight..."
    mkdir -p papers reports github logs data autodev_workspace hugo_site/public
    docker compose up -d
    sleep 2
    echo "[✓] 启动完成"
    echo ""
    echo "🌐 访问主页: http://localhost:8084"
    echo "📊 状态监控: http://localhost:8084/status"
}

stop() {
    echo "[*] 停止 Paper Insight..."
    docker compose down
    echo "[✓] 已停止"
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if docker ps --format '{{.Names}}' | grep -q paper-insight; then
        echo -e "${GREEN}[✓] 容器运行中${NC}"
        docker compose ps
        echo ""
        echo "🌐 访问主页: http://localhost:8084"
        echo "📊 状态监控: http://localhost:8084/status"
    else
        echo -e "${RED}[✗] 容器未运行${NC}"
        echo "   使用 ./run.sh start 启动"
    fi
}

logs() {
    shift
    docker compose logs -f "$@"
}

deploy() {
    echo "[*] 一键部署（重新构建）..."
    mkdir -p papers reports github logs data autodev_workspace hugo_site/public
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}[!] .env 已创建，请编辑填入 ANTHROPIC_AUTH_TOKEN${NC}"
    fi
    docker compose down
    docker compose up -d --build
    sleep 3
    echo ""
    echo -e "${GREEN}[✓] 部署完成${NC}"
    echo ""
    echo "🌐 访问主页: http://localhost:8084"
    echo "📊 状态监控: http://localhost:8084/status"
    docker compose logs --tail=20
}

# 主入口
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$@"
        ;;
    deploy)
        deploy
        ;;
    *)
        show_help
        ;;
esac
