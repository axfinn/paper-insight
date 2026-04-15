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
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[!] 已在运行 (PID: $OLD_PID)，退出。"
        exit 1
    else
        echo "[*] 删除 stale 锁文件..."
        rm -f "$LOCK_FILE"
    fi
fi
echo $$ > "$LOCK_FILE"
trap "rm -f '$LOCK_FILE'; exit 0" EXIT INT TERM

# ─── 自动下载 autodev ───
install_autodev() {
    if [ -d "$SCRIPT_DIR/clawtest/autodev" ]; then
        return 0
    fi
    echo "[*] 克隆 autodev..."
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
        echo "[!] Claude Code 未登录"
        exit 1
    fi
    pip install beautifulsoup4 pyyaml requests -q 2>/dev/null || true
    echo "[✓] 依赖检查通过"
}

do_cleanup() { python3 scripts/cleanup.py; }
do_fetch_papers() { python3 scripts/paper_fetcher.py; }
do_fetch_github() { python3 scripts/github_fetcher.py --all; }
do_analyze_papers() { python3 scripts/paper_analyzer.py; }
do_analyze_github() { python3 scripts/github_analyzer.py --all; }
do_build_hugo() { python3 scripts/hugo_builder.py; }

start_server() {
    echo "[*] 启动服务器 :8084 ..."
    cd "$SCRIPT_DIR"
    PYTHONPATH="$SCRIPT_DIR" python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from scripts.server import main
main()
" &
    SERVER_PID=$!
    echo "[*] 服务器 PID: $SERVER_PID"
    sleep 2
}

# ─── 持续运行模式 ───
run_continuous() {
    check_deps
    FETCH_INTERVAL=${FETCH_INTERVAL:-7200}

    echo """
╔══════════════════════════════════════════════════════════════╗
║              Paper Insight 持续运行模式                       ║
║  抓取间隔: \$((FETCH_INTERVAL/3600)) 小时                                        ║
╚══════════════════════════════════════════════════════════════╝
    """

    mkdir -p "$SCRIPT_DIR/hugo_site/public"
    do_build_hugo
    start_server

    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] === 开始抓取 ==="
        do_fetch_papers
        do_fetch_github
        do_analyze_papers
        do_analyze_github
        do_build_hugo
        do_cleanup
        echo "[$timestamp] === 本轮完成，等待 ${FETCH_INTERVAL}s ==="
        sleep $FETCH_INTERVAL
    done
}

# ─── Autodev 模式 ───
run_autodev_loop() {
    install_autodev
    mkdir -p "$SCRIPT_DIR/autodev_workspace"

    echo """
╔══════════════════════════════════════════════════════════════╗
║              Paper Insight + AutoDev 任务模式                 ║
╚══════════════════════════════════════════════════════════════╝
    """

    mkdir -p "$SCRIPT_DIR/hugo_site/public"
    do_build_hugo
    start_server

    AUTODEV_DIR="$SCRIPT_DIR/clawtest/autodev"
    AUTODEV_WORKSPACE="$SCRIPT_DIR/autodev_workspace"

    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] === 开始抓取 ==="
        do_fetch_papers
        do_fetch_github

        echo "[$timestamp] === 开始 AI 分析（autodev）==="
        TASK="分析 papers/ 目录下的今日论文数据，生成报告到 reports/ 目录。"

        cd "$AUTODEV_DIR"
        ./autodev "$TASK" --path "$AUTODEV_WORKSPACE/paper-analysis-$(date +%m%d-%H%M)" --publish 2>&1 || {
            echo "[!] autodev 异常，切换到 Python 模式..."
            do_analyze_papers
            do_analyze_github
        }

        do_build_hugo
        do_cleanup
        echo "[$timestamp] === 本轮完成 ==="
        sleep $FETCH_INTERVAL
    done
}

# ─── 主入口 ───
case "${1:-usage}" in
    once)
        check_deps
        do_cleanup
        do_fetch_papers
        do_fetch_github
        do_analyze_papers
        do_analyze_github
        do_build_hugo
        ;;
    continuous)
        run_continuous
        ;;
    autodev)
        FETCH_INTERVAL=${FETCH_INTERVAL:-7200}
        run_autodev_loop
        ;;
    hugo)
        do_build_hugo
        ;;
    cleanup)
        do_cleanup
        ;;
    *)
        echo "用法: ./start.sh {once|continuous|autodev|hugo|cleanup}"
        ;;
esac
