#!/bin/bash
# Paper Insight 一键部署脚本
# 在新机器上运行此脚本即可完成部署

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Paper Insight 一键部署                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ─── 1. 克隆项目 ───
if [ ! -d "paper-insight" ]; then
    echo "[*] 克隆 Paper Insight..."
    git clone https://github.com/axfinn/clawtest.git paper-insight 2>/dev/null || \
    git clone git@github.com:axfinn/clawtest.git paper-insight
fi

cd paper-insight

# ─── 2. 检查 Docker ───
if ! command -v docker &> /dev/null; then
    echo "[*] 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[*] 安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# ─── 3. 启动 ───
echo "[*] 启动 Paper Insight..."
docker-compose up -d --build

# ─── 4. 完成 ───
echo """
╔══════════════════════════════════════════════════════════════╗
║              ✅ 部署完成                                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  查看日志: docker-compose logs -f                             ║
║  停止服务: docker-compose down                                ║
║                                                              ║
║  报告目录: ./reports/                                        ║
║  网站目录: ./hugo_site/public/                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
