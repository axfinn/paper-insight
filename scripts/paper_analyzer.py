#!/usr/bin/env python3
"""
论文分析器 - 调用 Claude API 分析论文
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_paper(paper: dict, industry: str, api_key: str = None) -> dict:
    """使用 Claude 分析单篇论文"""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))

    prompt = f"""你是一位专业的行业研究员。请深度分析以下{industry}领域的论文，提取完整信息。

论文标题: {paper.get('title', 'N/A')}
作者: {', '.join(paper.get('authors', [])[:5])}
来源: {paper.get('source', 'N/A')}
发表日期: {paper.get('published', 'N/A')}
期刊/会议: {paper.get('journal', 'N/A')}

原始摘要:
{paper.get('summary', 'N/A')}

请深度分析并返回以下信息（JSON格式）：
{{
    "title": "论文标题",
    "problem": "论文要解决什么问题？为什么这个问题重要？",
    "background": "背景：之前的方法是什么，有什么局限性？",
    "method": "本文的核心方法/技术是什么？具体创新点是什么？",
    "novelty": "最大的创新点/突破是什么？相比之前工作的本质区别？",
    "results": "实验结果如何？关键数据指标？",
    "application": "实际应用场景和商业价值",
    "limitations": "论文的局限性/缺点/未解决的问题",
    "future": "未来改进方向和研究机会",
    "rating": "1-5分的行业影响力评分（5=必读，1=可忽略）",
    "difficulty": "学习难度 1-5（1=入门级，5=专家级）",
    "tags": ["相关领域标签1", "标签2", "标签3"],
    "must_read": true/false  # 是否值得精读
}}

只返回JSON，不要其他内容。"""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.content[0].text)
        return {**paper, **result, 'analyzed': True}
    except Exception as e:
        print(f"  [!] Analysis error: {e}")
        return {**paper, 'analyzed': False, 'error': str(e)}


def analyze_industry_papers(industry: str, papers: list, api_key: str = None) -> list:
    """分析一个行业的所有论文"""
    analyzed = []

    for i, paper in enumerate(papers):
        print(f"  Analyzing [{i+1}/{len(papers)}]: {paper.get('title', '')[:50]}...")
        result = analyze_paper(paper, industry, api_key)
        analyzed.append(result)

    return analyzed


def generate_report(industry: str, papers: list) -> str:
    """生成 Markdown 报告"""

    # 按评分排序
    sorted_papers = sorted(papers, key=lambda x: x.get('rating', 0), reverse=True)

    # 统计
    total = len(papers)
    analyzed = sum(1 for p in papers if p.get('analyzed'))
    must_read = sum(1 for p in papers if p.get('must_read'))

    report = f"""# {industry} 论文情报

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**抓取数量**: {total} 篇 | **分析完成**: {analyzed} 篇 | **必读**: {must_read} 篇

---

## 📖 必读论文

"""

    # 先输出必读论文
    for i, paper in enumerate([p for p in sorted_papers if p.get('must_read')], 1):
        if paper.get('analyzed'):
            report += f"""### 🔥 {i}. {paper.get('title', 'N/A')}

| 属性 | 内容 |
|------|------|
| **评分** | {'⭐' * paper.get('rating', 0)} ({paper.get('rating', 0)}/5) |
| **难度** | {'🔒' * paper.get('difficulty', 0)} ({paper.get('difficulty', 0)}/5) |
| **作者** | {', '.join(paper.get('authors', [])[:3])} |
| **来源** | {paper.get('source', 'N/A')} |
| **发表** | {paper.get('published', 'N/A')} |

### 研究问题
{paper.get('problem', 'N/A')}

### 背景
{paper.get('background', 'N/A')}

### 核心方法
{paper.get('method', 'N/A')}

### 关键创新点
{paper.get('novelty', 'N/A')}

### 实验结果
{paper.get('results', 'N/A')}

### 应用场景
{paper.get('application', 'N/A')}

### 局限性
{paper.get('limitations', 'N/A')}

### 未来方向
{paper.get('future', 'N/A')}

**标签**: {', '.join(paper.get('tags', []))}

[原文链接]({paper.get('url', '#')})

---

"""

    # 其他重要论文
    other_important = [p for p in sorted_papers if p.get('rating', 0) >= 3 and not p.get('must_read')]
    if other_important:
        report += f"""## ⭐ 重要论文

"""
        for i, paper in enumerate(other_important, 1):
            if paper.get('analyzed'):
                report += f"""### {i}. {paper.get('title', 'N/A')}

**评分**: {'⭐' * paper.get('rating', 0)} ({paper.get('rating', 0)}/5) | **难度**: {'🔒' * paper.get('difficulty', 0)}

**问题**: {paper.get('problem', 'N/A')[:150]}...

**方法**: {paper.get('method', 'N/A')[:150]}...

**创新点**: {paper.get('novelty', 'N/A')[:150]}...

[原文链接]({paper.get('url', '#')})

---

"""

    # 其他论文列表
    other_papers = [p for p in sorted_papers if p.get('rating', 0) < 3]
    if other_papers:
        report += f"""## 📋 其他论文

| # | 标题 | 评分 | 难度 | 来源 |
|---|------|------|------|------|
"""
        for i, paper in enumerate(other_papers, 1):
            title = paper.get('title', 'N/A')[:45] + '...' if len(paper.get('title', '')) > 45 else paper.get('title', 'N/A')
            rating = paper.get('rating', 0) if paper.get('analyzed') else '⏳'
            diff = paper.get('difficulty', 0) if paper.get('analyzed') else '?'
            report += f"| {i} | {title} | {rating} | {diff} | {paper.get('source', 'N/A')} |\n"

    return report

    # 其他论文列表
    if len(sorted_papers) > 5:
        report += f"""## 其他论文

| # | 标题 | 评分 | 来源 | 发表日期 |
|---|------|------|------|----------|
"""
        for i, paper in enumerate(sorted_papers[5:], 6):
            title = paper.get('title', 'N/A')[:40] + '...' if len(paper.get('title', '')) > 40 else paper.get('title', 'N/A')
            rating = paper.get('rating', 0) if paper.get('analyzed') else '⏳'
            report += f"| {i} | {title} | {rating} | {paper.get('source', 'N/A')} | {paper.get('published', 'N/A')} |\n"

    return report


def main():
    papers_dir = Path(__file__).parent.parent / 'papers'
    reports_dir = Path(__file__).parent.parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    # 获取最新的论文文件
    today = datetime.now().strftime('%Y%m%d')

    # 分析所有行业的论文
    for paper_file in papers_dir.glob(f"{today}_*.json"):
        print(f"\n[*] Analyzing {paper_file.name}...")

        with open(paper_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        industry = data['industry']
        papers = data['papers']

        # 分析论文
        analyzed = analyze_industry_papers(industry, papers)

        # 生成报告
        report = generate_report(industry, analyzed)

        # 保存报告
        report_file = reports_dir / f"{today}_{industry.replace('/', '_')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"[+] Report saved: {report_file}")

        # 保存分析后的数据
        data_file = reports_dir / f"{today}_{industry.replace('/', '_')}_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({'industry': industry, 'papers': analyzed, 'generated_at': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

    print("\n[+] All reports generated!")


if __name__ == '__main__':
    main()
