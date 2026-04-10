#!/bin/bash
# Paper Insight 启动脚本
# 集成 autodev 实现自主迭代开发

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ─── 自动下载 autodev ───
install_autodev() {
    if [ -d "$SCRIPT_DIR/clawtest/autodev" ]; then
        return 0
    fi

    echo "[*] 从 GitHub 克隆 autodev..."
    git clone --quiet https://github.com/axfinn/clawtest.git "$SCRIPT_DIR/clawtest"

    chmod +x "$SCRIPT_DIR/clawtest/autodev/autodev" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/clawtest/autodev/autodev-stop" 2>/dev/null || true

    echo "[✓] autodev 安装完成"
}

# ─── 依赖检查 ───
check_deps() {
    echo "[*] 检查依赖..."

    if ! command -v claude &> /dev/null; then
        echo "[!] Claude Code CLI 未安装"
        exit 1
    fi

    if ! claude --version &> /dev/null; then
        echo "[!] Claude Code 未登录，请先运行 claude auth"
        exit 1
    fi

    # 自动安装 autodev（如果使用 autodev 模式）
    if [[ "$*" == *"autodev"* ]]; then
        install_autodev
    fi

    # Python 依赖
    pip install beautifulsoup4 pyyaml requests -q 2>/dev/null || true

    echo "[✓] 依赖检查通过"
}

# ─── 磁盘清理 ───
do_cleanup() {
    echo "[*] 执行磁盘清理..."
    python3 scripts/cleanup.py
}

# ─── 抓取论文 ───
do_fetch_papers() {
    echo "[*] 抓取论文..."
    python3 scripts/paper_fetcher.py
}

# ─── 抓取 GitHub ───
do_fetch_github() {
    echo "[*] 抓取 GitHub Trending..."
    python3 scripts/github_fetcher.py --all
}

# ─── 生成论文报告 ───
do_analyze_papers() {
    echo "[*] AI 分析论文..."
    python3 scripts/paper_analyzer.py
}

# ─── 生成 GitHub 报告 ───
do_analyze_github() {
    echo "[*] AI 分析 GitHub 项目..."
    python3 scripts/github_analyzer.py --all
}

# ─── 构建 Hugo 网站 ───
do_build_hugo() {
    echo "[*] 构建 Hugo 网站..."
    python3 scripts/hugo_builder.py
}

# ─── 单次运行 ───
run_once() {
    check_deps
    do_cleanup
    do_fetch_papers
    do_fetch_github
    do_analyze_papers
    do_analyze_github
    do_build_hugo
    echo "[✓] 本轮完成"
}

# ─── 持续运行模式 ───
run_continuous() {
    check_deps

    FETCH_INTERVAL=${FETCH_INTERVAL:-7200}  # 默认 2 小时抓取一次
    ANALYSIS_INTERVAL=${ANALYSIS_INTERVAL:-1800}  # 默认 30 分钟分析一次

    echo """
╔══════════════════════════════════════════════════════════════╗
║              Paper Insight 持续运行模式                       ║
║                                                              ║
║  抓取间隔: $((FETCH_INTERVAL/3600)) 小时                                        ║
║  分析间隔: $((ANALYSIS_INTERVAL/60)) 分钟                                        ║
║                                                              ║
║  Ctrl+C 停止                                                ║
╚══════════════════════════════════════════════════════════════╝
    """

    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] === 开始抓取 ==="

        # 抓取
        do_fetch_papers
        do_fetch_github

        # 每次抓取后分析
        do_analyze_papers
        do_analyze_github

        # 构建网站
        do_build_hugo

        # 清理
        do_cleanup

        echo "[$timestamp] === 本轮完成，等待 ${FETCH_INTERVAL}s ==="
        sleep $FETCH_INTERVAL
    done
}

# ─── Autodev 自主迭代模式 ───
run_autodev_loop() {
    echo """
╔══════════════════════════════════════════════════════════════╗
║              Paper Insight + AutoDev 任务模式                 ║
║                                                              ║
║  运行: 抓取 + AI 分析 + 生成报告（持续循环）                   ║
║                                                              ║
║  停止: Ctrl+C                                               ║
╚══════════════════════════════════════════════════════════════╝
    """

    # 直接运行 continuous 模式的任务（使用 MiniMax API 分析）
    run_continuous
}

# ─── 使用说明 ───
usage() {
    echo """
Paper Insight - 论文情报站 + GitHub Trending 分析

用法:
    ./start.sh once         单次运行（抓取 + 分析 + 构建网站）
    ./start.sh continuous   持续运行（定时抓取 + 分析 + 构建网站）
    ./start.sh autodev      AutoDev 任务模式（持续抓取 + AI 分析）
    ./start.sh hugo         仅构建 Hugo 网站
    ./start.sh cleanup      仅执行磁盘清理

环境变量:
    FETCH_INTERVAL      抓取间隔（秒），默认 7200（2小时）
    ANALYSIS_INTERVAL   分析间隔（秒），默认 1800（30分钟）

Docker 部署:
    docker-compose up -d          # 启动
    docker-compose logs -f       # 查看日志
    docker-compose down           # 停止
"""
}

# ─── 主入口 ───
case "${1:-usage}" in
    once)
        run_once
        ;;
    continuous)
        run_continuous
        ;;
    autodev)
        run_autodev_loop
        ;;
    hugo)
        do_build_hugo
        ;;
    cleanup)
        do_cleanup
        ;;
    *)
        usage
        ;;
esac
