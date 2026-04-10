#!/bin/bash
# Paper Insight 部署脚本
# 在项目目录下运行此脚本即可完成部署

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Paper Insight 部署脚本                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ─── 1. 创建必要文件 ───
echo "[*] 检查配置文件..."

# 创建 .env 文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "[!] .env 已创建，请编辑填入 ANTHROPIC_AUTH_TOKEN"
        echo "[*] 示例: ANTHROPIC_AUTH_TOKEN=sk-xxx"
    fi
fi

# 创建必要目录
mkdir -p papers reports github logs data autodev_workspace hugo_site/public

# ─── 2. 拉取最新代码 ───
echo "[*] 拉取最新代码..."
git pull 2>/dev/null || echo "[*] 非 git 仓库或无远程"

# ─── 3. 构建并启动 ───
echo "[*] 构建并启动 Docker..."

if docker compose version &> /dev/null; then
    docker compose down
    docker compose up -d --build
elif docker-compose version &> /dev/null; then
    docker-compose down
    docker-compose up -d --build
else
    echo "[!] Docker Compose not found"
    exit 1
fi

# ─── 4. 等待服务启动 ───
echo "[*] 等待服务启动..."
sleep 5

# ─── 5. 显示状态 ───
echo """
╔══════════════════════════════════════════════════════════════╗
║              ✅ 部署完成                                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  查看日志: docker compose logs -f                            ║
║  停止服务: docker compose down                               ║
║                                                              ║
║  访问: http://localhost:8084                                ║
║                                                              ║
║  注意: 首次运行需要等待 autodev 完成抓取和分析               ║
║        可能需要几分钟到几十分钟                               ║
╚══════════════════════════════════════════════════════════════╝
"""

# 显示日志
docker compose logs --tail=30
