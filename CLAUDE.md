# Paper Insight - Claude Code 工作目录

## 项目位置
```
/home/hejiahao01/code/bili/work/paper-insight/
```

## 项目目标
Paper Insight 是一款 AI 驱动的情报自动化工具，追踪 7 大前沿领域的最新学术论文和 GitHub 开源项目。

## 目录结构
```
paper-insight/
├── scripts/
│   ├── paper_fetcher.py      # 论文爬虫（arXiv/PubMed/Semantic Scholar）
│   ├── paper_analyzer.py     # 论文 AI 分析
│   ├── github_fetcher.py     # GitHub Trending 爬虫
│   ├── github_analyzer.py    # GitHub AI 分析（排行榜）
│   ├── hugo_builder.py       # Hugo 网站构建
│   ├── cleanup.py            # 磁盘清理
│   └── main_runner.py        # 主运行器
├── config/
│   └── industries.yaml       # 行业配置
├── reports/                  # 生成的报告
├── papers/                   # 原始论文数据
├── github/                   # GitHub 项目数据
└── hugo_site/               # Hugo 网站
```

## 两种运行模式

### 1. 采集模式（自动运行，不需要 AI）
```bash
./start.sh once         # 单次采集 + 分析
./start.sh continuous   # 持续采集（定时运行）
```
这是 Python 脚本执行，不需要 Claude Code。

### 2. 改进模式（使用 AutoDev）
```bash
./start.sh autodev
```
这是让 AutoDev 改进项目代码本身（优化爬虫、分析逻辑等）。

## AutoDev 使用边界

⚠️ **重要**：当使用 autodev 改进项目时，必须遵循以下边界：

### DISCOVER 阶段
- 扫描 `scripts/` 目录理解现有代码结构
- 搜索相关技术方案
- **禁止**：修改任何代码文件

### DEFINE 阶段
- 明确改进目标（如：提高爬虫效率、优化分析质量）
- **禁止**：写实现代码

### DESIGN 阶段
- 制定改进方案
- **禁止**：写实现代码

### DO 阶段
- 按设计方案修改 `scripts/` 下的 Python 文件
- 确保代码可运行
- **禁止**：修改 `start.sh` 以外的业务流程

### REVIEW 阶段
- 验证修改是否正确
- **禁止**：大幅重写

### DELIVER 阶段
- 提交 git commit
- 更新相关文档

## 成功标准

改进交付时必须满足：
1. Python 脚本可正常运行（`python3 scripts/xxx.py` 不报错）
2. 报告格式正确（Markdown 结构完整）
3. 磁盘清理正常工作
4. git commit 记录变更

## 行业配置

修改 `config/industries.yaml` 时注意：
- 只修改关键词和分类，不要改变文件格式
- 新增行业需要同时更新 `paper_fetcher.py` 的数据源映射
