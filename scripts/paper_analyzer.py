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

    prompt = f"""你是一位专业的行业分析师。请分析以下{industry}领域的论文，并提取关键信息。

论文标题: {paper.get('title', 'N/A')}
作者: {', '.join(paper.get('authors', [])[:5])}
来源: {paper.get('source', 'N/A')}
发表日期: {paper.get('published', 'N/A')}
期刊/会议: {paper.get('journal', 'N/A')}

摘要:
{paper.get('summary', 'N/A')}

请分析并返回以下信息（JSON格式）：
{{
    "title": "论文标题",
    "summary": "100字内的核心摘要",
    "innovation": "主要创新点",
    "method": "核心技术方法",
    "application": "应用场景/商业价值",
    "limitations": "局限性/风险",
    "rating": "1-5分的行业影响力评分",
    "tags": ["相关标签1", "标签2"]
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

    report = f"""# {industry} 论文情报
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**论文数量**: {len(papers)}

---

## 重点论文 TOP 5

"""

    for i, paper in enumerate(sorted_papers[:5], 1):
        if paper.get('analyzed'):
            report += f"""### {i}. {paper.get('title', 'N/A')}

**评分**: {'⭐' * paper.get('rating', 0)} ({paper.get('rating', 0)}/5)
**作者**: {', '.join(paper.get('authors', [])[:3])}
**来源**: {paper.get('source', 'N/A')} | {paper.get('published', 'N/A')}

**摘要**: {paper.get('summary', 'N/A')}

**创新点**: {paper.get('innovation', 'N/A')}

**技术方法**: {paper.get('method', 'N/A')}

**应用场景**: {paper.get('application', 'N/A')}

**局限性**: {paper.get('limitations', 'N/A')}

**标签**: {', '.join(paper.get('tags', []))}

[原文链接]({paper.get('url', '#')})

---

"""

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
