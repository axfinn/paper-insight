# Paper Insight

AI 驱动的多行业论文情报站 + GitHub Trending 分析器。自动抓取最新论文和开源项目，AI 分析生成有价值的排行榜和报告。

## 特性

- **7 大行业覆盖**: AI/ML、医疗健康、金融、新能源、半导体、消费、游戏
- **4 大数据源**: arXiv、PubMed、Semantic Scholar、GitHub Trending
- **AI 智能分析**: 创新点、技术栈、潜力评分、应用场景
- **GitHub 排行榜**: 按语言分类，潜力评分排序
- **Hugo 静态网站**: 自动生成可部署的静态站
- **AutoDev 集成**: 支持自主迭代，持续改进
- **磁盘清理**: 自动清理旧数据，防止爆盘
- **Docker 部署**: 一键部署，跨平台运行

## 快速开始

### 一键部署（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/axfinn/clawtest/master/paper-insight/deploy.sh | bash
```

### 手动部署

```bash
git clone https://github.com/axfinn/clawtest.git
cd clawtest/paper-insight
chmod +x deploy.sh
./deploy.sh
```

### 本地运行

```bash
./start.sh once         # 单次运行（抓取 + 分析 + 建站）
./start.sh continuous   # 持续运行（定时抓取）
./start.sh autodev     # AutoDev 自主迭代模式
```

## 使用场景

### 场景 1: 学术研究

每天自动抓取 AI/ML、医疗、新能源领域的最新论文，AI 生成摘要和创新点分析，帮助快速跟踪学术前沿。

### 场景 2: 技术选型

通过 GitHub Trending 排行榜，发现值得关注的新兴开源项目，了解技术趋势，辅助技术选型决策。

### 场景 3: 投资参考

追踪前沿技术领域（AI、半导体、新能源）的论文和项目，为投资决策提供技术情报支持。

## 数据源

| 数据源 | 类型 | 覆盖领域 |
|--------|------|----------|
| arXiv | 学术论文 | AI/ML、新能源、半导体 |
| PubMed | 医学论文 | 医疗健康 |
| Semantic Scholar | 学术论文 | 金融、消费、游戏 |
| GitHub Trending | 开源项目 | Python/Go/Rust/TS/JS |

## 行业覆盖

| 行业 | 数据源 | 关键词 |
|------|--------|--------|
| AI/ML | arXiv | machine learning, deep learning, LLM, transformer |
| 医疗健康 | PubMed | medical, healthcare, drug discovery |
| 金融 | Semantic Scholar | finance, trading, blockchain |
| 新能源/材料 | arXiv | solar, battery, hydrogen, catalyst |
| 半导体/芯片 | arXiv | semiconductor, chip, IC |
| 消费/电商 | Semantic Scholar | e-commerce, retail, recommendation |
| 游戏 | Semantic Scholar | gaming, graphics, VR |

## 报告示例

### 论文报告结构

```markdown
# AI/ML 论文情报

## 重点论文 TOP 5

### 🥇 BERT模型改进研究

**评分**: ⭐⭐⭐⭐⭐ (5/5) | **难度**: 🔒🔒 (2/5)

**创新点**: 提出新的注意力机制

**技术栈**: PyTorch, Transformer, BERT

**应用场景**: NLP 下游任务

**为什么有意思**: 显著提升推理速度
```

### GitHub 排行榜结构

```markdown
# GitHub Trending Python 排行榜

## 🏆 TOP 10 最值得关注的项目

### 🥇 awesome-ai-agent

**评分**: ⭐⭐⭐⭐⭐ (5/5) | **难度**: 🔒🔒🔒 (3/5)

**创新点**: 首个开源 AI Agent 框架

**技术栈**: Python, LangChain, OpenAI

**应用场景**: AI 应用开发
```

## 目录结构

```
paper-insight/
├── config/
│   └── industries.yaml       # 行业配置
├── scripts/
│   ├── paper_fetcher.py      # 论文爬虫
│   ├── paper_analyzer.py     # 论文 AI 分析
│   ├── github_fetcher.py     # GitHub 爬虫
│   ├── github_analyzer.py    # GitHub AI 分析（排行榜）
│   ├── hugo_builder.py       # Hugo 网站构建
│   ├── cleanup.py            # 磁盘清理
│   └── main_runner.py        # 主运行器
├── reports/                   # 生成的报告
├── papers/                    # 原始论文数据（JSON）
├── github/                    # GitHub 项目数据（JSON）
├── hugo_site/                # Hugo 网站源码
│   └── public/              # 生成的静态网站
├── Dockerfile               # Docker 构建
├── docker-compose.yml       # Docker Compose
├── deploy.sh                # 一键部署脚本
└── start.sh                 # 启动脚本
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FETCH_INTERVAL` | 7200 | 抓取间隔（秒），默认 2 小时 |
| `ANALYSIS_INTERVAL` | 1800 | 分析间隔（秒），默认 30 分钟 |

示例：

```bash
# 1 小时抓取一次
FETCH_INTERVAL=3600 ./start.sh continuous
```

## Docker 部署

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 重新构建
docker-compose up -d --build
```

## 磁盘管理

系统自动清理旧数据，防止磁盘爆满：

| 数据类型 | 保留时间 |
|----------|----------|
| 论文原始数据 | 7 天 |
| GitHub 原始数据 | 7 天 |
| 分析报告 | 30 天 |
| 日志文件 | 3 天 |
| AutoDev 项目 | 3 天 |

手动清理：

```bash
./start.sh cleanup
```

## 依赖

- Python 3.10+
- Docker & Docker Compose
- Hugo（Docker 部署时自动安装）
- Claude Code CLI（本地运行需要）

## 常见问题

### Q: 报 "Claude Code 未登录"

本地运行需要先登录 Claude Code：

```bash
claude auth
```

### Q: Docker 部署后看不到报告

报告生成需要时间，首次运行可能需要 5-10 分钟。用 `docker-compose logs -f` 查看进度。

### Q: 如何停止 AutoDev 迭代？

```bash
./clawtest/autodev/autodev-stop /tmp/paper-insight/loop
```

## License

MIT
