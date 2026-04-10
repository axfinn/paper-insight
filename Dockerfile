# Paper Insight - 论文情报站 + GitHub Trending 分析
# 支持 Docker 部署

FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    jq \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 安装 Hugo (用于静态网站生成)
RUN wget -q https://github.com/gohugoio/hugo/releases/download/v0.123.0/hugo_0.123.0_linux-amd64.tar.gz && \
    tar -xzf hugo_0.123.0_linux-amd64.tar.gz -C /tmp && \
    mv /tmp/hugo /usr/local/bin/hugo && \
    rm -f /tmp/hugo_0.123.0_linux-amd64.tar.gz && \
    chmod +x /usr/local/bin/hugo

# 安装 Claude Code CLI (Linux)
RUN npm install -g @anthropic-ai/claude-code && \
    ln -sf /usr/local/bin/claude /usr/bin/claude

# 验证 Claude CLI
RUN claude --version || echo "Claude CLI installed"

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/logs /app/reports

# 创建非 root 用户（避免挂载 ~/.claude 权限问题）
RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8084

# 默认运行持续模式（抓取 + 分析 + 构建网站）
CMD ["./start.sh", "continuous"]
