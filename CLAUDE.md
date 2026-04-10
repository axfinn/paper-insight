# Paper Insight - Claude Code 持续运行配置

## 项目目标
让 Claude Code 持续不间断地运行，自动抓取和分析多行业最新论文。

## 运行方式

### 方式一：直接运行 Python（推荐用于后台）

```bash
cd /home/hejiahao01/code/bili/work/paper-insight
export ANTHROPIC_API_KEY='your-key'
./start.sh continuous
```

### 方式二：Claude Code /loop 模式

在 Claude Code 中执行：

```
/loop 30m 在 paper-insight 目录下检查论文抓取进度，如有需要则运行 python scripts/main_runner.py --once
```

### 方式三：Cron 定时（每天定时抓取）

```bash
# 每天早上 8 点抓取一次
0 8 * * * cd /home/hejiahao01/code/bili/work/paper-insight && ANTHROPIC_API_KEY='your-key' python scripts/main_runner.py --once >> logs/cron.log 2>&1
```

## 自迭代机制

系统会每 10 次迭代自动检查：
1. 各行业分析成功率
2. 论文评分分布
3. 识别分析质量波动

## 行业覆盖
- AI/ML (arXiv: cs.AI, cs.LG, cs.CL, cs.CV)
- 医疗健康 (PubMed)
- 金融 (Semantic Scholar)
- 新能源/材料 (arXiv)
- 半导体/芯片 (arXiv)
- 消费/电商 (Semantic Scholar)
- 游戏 (Semantic Scholar)

## 数据流
```
定时触发 → 抓取论文 API → 保存 JSON → AI 分析 → 生成 Markdown 报告 → 更新首页
```
