#!/bin/bash
# Paper Insight 运行脚本
# 在项目目录下运行即可启动服务

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Paper Insight 启动                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[*] 创建 .env 文件..."
        cp .env.example .env
        echo "[!] 请编辑 .env 填入 ANTHROPIC_AUTH_TOKEN"
        echo "[*] 启动跳过，等待你配置..."
    fi
fi

# 创建必要目录
mkdir -p papers reports github logs data autodev_workspace hugo_site/public

# 检查 Docker
if ! docker compose version &> /dev/null; then
    echo "[!] Docker Compose not found"
    exit 1
fi

# 启动
echo "[*] 启动 Paper Insight..."
docker compose up -d

# 等待启动
sleep 3

# 显示状态
echo """
╔══════════════════════════════════════════════════════════════╗
║              ✅ 启动完成                                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  查看日志: docker compose logs -f                            ║
║  停止服务: docker compose down                               ║
║                                                              ║
║  访问: http://localhost:8084                                  ║
║  状态: http://localhost:8084/status                           ║
╚══════════════════════════════════════════════════════════════╝
"""

docker compose logs --tail=20
