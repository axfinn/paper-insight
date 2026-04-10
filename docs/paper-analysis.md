# 论文分析功能说明

## 概述

Paper Insight 的论文分析模块自动抓取 arXiv、PubMed、Semantic Scholar 的最新论文，并使用 Claude AI 进行深度分析，生成结构化的情报报告。

## 分析维度

每篇论文都会分析以下维度：

| 维度 | 说明 |
|------|------|
| **problem** | 论文要解决什么问题？为什么重要？ |
| **background** | 之前的方法是什么？有什么局限性？ |
| **method** | 本文的核心方法/技术是什么？ |
| **novelty** | 最大的创新点/突破是什么？ |
| **results** | 实验结果如何？关键数据指标？ |
| **application** | 实际应用场景和商业价值 |
| **limitations** | 论文的局限性/缺点/未解决的问题 |
| **future** | 未来改进方向和研究机会 |
| **rating** | 行业影响力评分 1-5（5=必读） |
| **difficulty** | 学习难度 1-5（1=入门，5=专家） |
| **must_read** | 是否值得精读（true/false） |
| **tags** | 相关领域标签 |

## 报告结构

### 1. 必读论文（must_read = true）
完整分析，包含：
- 研究问题
- 背景
- 核心方法
- 关键创新点
- 实验结果
- 应用场景
- 局限性
- 未来方向

### 2. 重要论文（rating >= 3）
简要分析，包含核心问题、方法、创新点摘要。

### 3. 其他论文（rating < 3）
表格形式展示，标题、评分、难度、来源。

## 示例

```markdown
# AI/ML 论文情报

**生成时间**: 2026-04-10 12:00:00
**抓取数量**: 45 篇 | **分析完成**: 45 篇 | **必读**: 3 篇

---

## 📖 必读论文

### 🔥 1. Attention Is All You Need

| 属性 | 内容 |
|------|------|
| **评分** | ⭐⭐⭐⭐⭐ (5/5) |
| **难度** | 🔒🔒🔒 (3/5) |
| **作者** | Vaswani, Shazeer, Parmar, et al. |
| **来源** | arXiv |
| **发表** | 2017-06-12 |

### 研究问题
Transformer 架构要解决什么问题？

### 背景
RNN 在处理长序列时存在梯度消失问题，CNN 并行计算能力受限。

### 核心方法
提出 Transformer 架构，完全基于注意力机制，抛弃 RNN 和 CNN。

### 关键创新点
- Self-Attention 机制
- Multi-Head Attention
- Position-wise Feed-Forward Networks
- 位置编码

### 实验结果
在 WMT 2014 英德翻译任务上达到 28.4 BLEU，超过了当时所有模型。

### 应用场景
- 机器翻译
- 文本生成
- 语音识别
- 所有序列建模任务

### 局限性
- 注意力计算复杂度 O(n²)
- 位置编码是固定的，在某些任务上可能不是最优

### 未来方向
- 高效注意力机制
- 更长的上下文建模
```

## 数据源

| 数据源 | API | 覆盖领域 |
|--------|-----|----------|
| arXiv | https://export.arxiv.org/api/query | AI/ML、新能源、半导体 |
| PubMed | https://eutils.ncbi.nlm.nih.gov | 医疗健康 |
| Semantic Scholar | https://api.semanticscholar.org | 金融、消费、游戏 |

## 配置

修改 `config/industries.yaml` 调整：
- 关键词
- 抓取数量
- 数据源
