#!/bin/bash
# Paper Insight 启动脚本
# 集成 autodev 实现自主迭代开发

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量（MiniMax API 配置）
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ─── 进程锁（防止重复启动）───
LOCK_FILE="$SCRIPT_DIR/.autodev.lock"
if [ -f "$LOCK_FILE" ]; then
    OLD_PID=$(cat "$LOCK_FILE")
    # 检查进程是否还存在
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[!] autodev 已在运行 (PID: $OLD_PID)，退出。"
        exit 1
    else
        echo "[*] 发现 stale 锁文件，删除..."
        rm -f "$LOCK_FILE"
    fi
fi
# 写入当前进程 PID
echo $$ > "$LOCK_FILE"
trap "rm -f '$LOCK_FILE'; exit 0" EXIT INT TERM

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

    # 先构建 Hugo 网站（确保 public 目录存在）
    echo "[*] 初始构建 Hugo 网站..."
    do_build_hugo

    # 启动静态文件服务器（后台运行）
    echo "[*] 启动静态文件服务器 :8084 ..."
    python3 -m http.server 8084 --directory "$SCRIPT_DIR/hugo_site/public" &
    SERVER_PID=$!
    echo "[*] 服务器 PID: $SERVER_PID"

    # 等待服务器就绪
    sleep 2

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
    install_autodev

    echo """
╔══════════════════════════════════════════════════════════════╗
║              Paper Insight + AutoDev 任务模式                 ║
║                                                              ║
║  运行: 抓取 + AI 分析 + 生成报告（持续循环）                   ║
║                                                              ║
║  停止: Ctrl+C                                               ║
╚══════════════════════════════════════════════════════════════╝
    """

    AUTODEV_DIR="$SCRIPT_DIR/clawtest/autodev"
    AUTODEV_WORKSPACE="$SCRIPT_DIR/autodev_workspace"

    # 创建 autodev 工作区
    mkdir -p "$AUTODEV_WORKSPACE"

    # 启动静态文件服务器（后台运行）
    echo "[*] 启动静态文件服务器 :8084 ..."
    python3 -m http.server 8084 --directory "$SCRIPT_DIR/hugo_site/public" &
    SERVER_PID=$!
    echo "[*] 服务器 PID: $SERVER_PID"

    # 等待服务器就绪
    sleep 2

    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] === 开始抓取 ==="

        # 抓取论文
        do_fetch_papers

        # 抓取 GitHub
        do_fetch_github

        echo "[$timestamp] === 开始 AI 分析（autodev）==="

        # 使用 autodev 分析论文
        # 任务：分析 papers/ 目录，生成报告到 reports/
        TASK="分析 paper-insight 项目 papers/ 目录下的今日论文数据，生成分析报告到 reports/ 目录。要求：
1. 读取 papers/*.json 文件了解今日抓取的论文
2. 对每篇论文进行深度分析（问题、背景、方法、创新点、结果、局限性）
3. 按行业生成 Markdown 报告到 reports/ 目录
4. 必读论文要有完整详细分析，其他论文要有摘要
5. 最终生成 reports/RESULT.md 汇总所有分析结果"

        cd "$AUTODEV_DIR"
        ./autodev "$TASK" --path "$AUTODEV_WORKSPACE/paper-analysis-$(date +%m%d-%H%M)" --publish 2>&1 || {
            echo "[!] autodev 执行异常，切换到 Python 脚本模式..."
            do_analyze_papers
            do_analyze_github
        }

        # Hugo 建站
        do_build_hugo

        # 清理
        do_cleanup

        echo "[$timestamp] === 本轮完成，等待 ${FETCH_INTERVAL}s ==="
        sleep $FETCH_INTERVAL
    done
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
