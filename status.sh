#!/bin/bash
# Paper Insight 状态查看

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Paper Insight 状态                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 检查容器状态
if docker ps --format '{{.Names}}' | grep -q paper-insight; then
    echo "[✓] 容器运行中"
    docker compose ps
    echo ""
    echo "🌐 访问主页: http://localhost:8084"
    echo "📊 状态监控: http://localhost:8084/status"
else
    echo "[✗] 容器未运行"
    echo "   使用 ./run.sh 启动"
fi
