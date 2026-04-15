#!/usr/bin/env python3
"""
论文分析器 - 调用 Claude/MiniMax API 分析论文
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入配置
try:
    import yaml
    config_path = Path(__file__).parent.parent / 'config' / 'local.yaml'
    if config_path.exists():
        with open(config_path, 'r') as f:
            LOCAL_CONFIG = yaml.safe_load(f)
    else:
        LOCAL_CONFIG = {}
except:
    LOCAL_CONFIG = {}

def get_ai_config() -> dict:
    """获取 AI 配置"""
    ai = LOCAL_CONFIG.get('ai', {})
    return {
        'api_url': ai.get('api_url') or os.environ.get('AI_API_URL', 'https://api.minimaxi.com/anthropic'),
        'api_key': ai.get('api_key') or os.environ.get('MINIMAX_API_KEY') or os.environ.get('ANTHROPIC_API_KEY', ''),
        'model': ai.get('model', 'claude-3-5-haiku-20241022'),
    }


def analyze_paper(paper: dict, industry: str, api_key: str = None) -> dict:
    """使用 AI API 分析单篇论文"""
    import anthropic

    config = get_ai_config()
    api_key = api_key or config['api_key']

    # 使用 MiniMax/Claude 兼容接口
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=config['api_url'] if config['api_url'] != 'https://api.anthropic.com/v1' else None
    )

    prompt = f"""你是一位专业的行业研究员。请深度分析以下{industry}领域的论文，提取完整信息。**全部用中文回答**。

论文标题: {paper.get('title', 'N/A')}
作者: {', '.join(paper.get('authors', [])[:5])}
来源: {paper.get('source', 'N/A')}
发表日期: {paper.get('published', 'N/A')}
期刊/会议: {paper.get('journal', 'N/A')}

原始摘要（英文）:
{paper.get('summary', 'N/A')}

请深度分析并返回以下信息（JSON格式）：
{{
    "title": "论文标题（保留英文原标题）",
    "title_zh": "论文标题中文翻译",
    "summary_zh": "摘要中文翻译（完整翻译原文摘要）",
    "problem": "论文要解决什么问题？为什么这个问题重要？",
    "background": "背景：之前的方法是什么，有什么局限性？",
    "method": "本文的核心方法/技术是什么？具体创新点是什么？",
    "novelty": "最大的创新点/突破是什么？相比之前工作的本质区别？",
    "results": "实验结果如何？关键数据指标？",
    "application": "实际应用场景和商业价值。",
    "limitations": "论文的局限性/缺点/未解决的问题。",
    "future": "未来改进方向和研究机会。",
    "rating": 4,
    "difficulty": 3,
    "tags": ["相关领域标签1", "标签2", "标签3"],
    "must_read": true
}}

只返回JSON，不要其他内容。"""

    try:
        response = client.messages.create(
            model=config['model'],
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        # 提取响应文本（兼容 MiniMax 格式）
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text = block.text
                break
            elif hasattr(block, 'thinking'):
                # MiniMax 可能有思考块，忽略
                continue

        if not response_text:
            return {**paper, 'analyzed': False, 'error': 'Empty response from API'}

        # 去掉可能的 markdown 代码块包裹
        text = response_text.strip()
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()

        result = json.loads(text)
        return {**paper, **result, 'analyzed': True}
    except json.JSONDecodeError as e:
        # JSON 解析失败，尝试修复截断的 JSON
        if '"' in str(e) or "'" in str(e):
            # 可能输出被截断，尝试修复
            try:
                # 找到最后一个完整的字段
                text_trimmed = text[:e.pos] if e.pos else text
                # 尝试补全字符串
                text_trimmed = text_trimmed.rsplit(',', 1)[0]
                # 尝试补全对象
                brace_count = text_trimmed.count('{') - text_trimmed.count('}')
                if brace_count > 0:
                    text_trimmed += '}' * brace_count
                result = json.loads(text_trimmed)
                return {**paper, **result, 'analyzed': True, 'truncated': True}
            except:
                pass
        print(f"  [!] JSON 解析错误: {e}")
        return {**paper, 'analyzed': False, 'error': f'JSONDecodeError: {e}'}
    except Exception as e:
        err_str = str(e)
        if '529' in err_str or 'overloaded' in err_str.lower():
            print(f"  [!] API 过载，等待后重试...")
            import time
            time.sleep(5)
            return analyze_paper(paper, industry, api_key)  # 重试一次
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

    today_fmt = datetime.now().strftime('%Y-%m-%d')
    now_fmt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 按评分排序（rating 可能是字符串）
    def get_rating(p):
        r = p.get('rating', 0)
        try:
            return int(r)
        except (TypeError, ValueError):
            return 0

    sorted_papers = sorted(papers, key=get_rating, reverse=True)

    # 统计
    total = len(papers)
    analyzed = sum(1 for p in papers if p.get('analyzed'))
    must_read = sum(1 for p in papers if p.get('must_read'))

    report = f"""---
title: "{industry} 论文情报"
date: "{today_fmt}"
industry: "{industry}"
summary: "收录 {total} 篇最新论文"
---

# {industry} 论文情报

**生成时间**: {now_fmt}
**抓取数量**: {total} 篇 | **分析完成**: {analyzed} 篇 | **必读**: {must_read} 篇

---

## 📖 必读论文

"""

    # 先输出必读论文
    for i, paper in enumerate([p for p in sorted_papers if p.get('must_read')], 1):
        if paper.get('analyzed'):
            title_zh = paper.get('title_zh', '')
            title_display = f"{paper.get('title', 'N/A')}"
            if title_zh:
                title_display += f"\n> {title_zh}"
            report += f"""### 🔥 {i}. {paper.get('title', 'N/A')}

> **{paper.get('title_zh', '')}**

| 属性 | 内容 |
|------|------|
| **评分** | {'⭐' * int(paper.get('rating', 0))} ({paper.get('rating', 0)}/5) |
| **难度** | {'🔒' * int(paper.get('difficulty', 0))} ({paper.get('difficulty', 0)}/5) |
| **作者** | {', '.join(paper.get('authors', [])[:3])} |
| **来源** | {paper.get('source', 'N/A')} |
| **发表** | {paper.get('published', 'N/A')} |

#### 摘要（中文）
{paper.get('summary_zh', paper.get('summary', 'N/A'))}

<details>
<summary>原文摘要（English Abstract）</summary>

{paper.get('summary', 'N/A')}

</details>

#### 研究问题
{paper.get('problem', 'N/A')}

#### 背景
{paper.get('background', 'N/A')}

#### 核心方法
{paper.get('method', 'N/A')}

#### 关键创新点
{paper.get('novelty', 'N/A')}

#### 实验结果
{paper.get('results', 'N/A')}

#### 应用场景
{paper.get('application', 'N/A')}

#### 局限性
{paper.get('limitations', 'N/A')}

#### 未来方向
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
                title_zh = paper.get('title_zh', '')
                report += f"""### {i}. {paper.get('title', 'N/A')}
{">" + " **" + title_zh + "**" if title_zh else ""}

**评分**: {'⭐' * int(paper.get('rating', 0))} ({paper.get('rating', 0)}/5) | **难度**: {'🔒' * int(paper.get('difficulty', 0))}

**问题**: {paper.get('problem', 'N/A')[:200]}

**方法**: {paper.get('method', 'N/A')[:200]}

**创新点**: {paper.get('novelty', 'N/A')[:200]}

<details>
<summary>原文摘要（English Abstract）</summary>

{paper.get('summary', 'N/A')}

</details>

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


def main():
    papers_dir = Path(__file__).parent.parent / 'papers'
    reports_dir = Path(__file__).parent.parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    # 获取今天的日期
    today = datetime.now().strftime('%Y%m%d')

    # 分析所有行业的论文
    for paper_file in papers_dir.glob(f"{today}_*.json"):
        print(f"\n[*] Analyzing {paper_file.name}...")

        with open(paper_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        industry = data['industry']
        new_papers = data['papers']

        # 读取已分析的结果（避免重复分析）
        data_file = reports_dir / f"{today}_{industry.replace('/', '_')}_data.json"
        analyzed_map = {}
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                for p in old_data.get('papers', []):
                    if p.get('title'):
                        analyzed_map[p['title']] = p
            print(f"  [*] 已存在 {len(analyzed_map)} 篇已分析论文")

        # 只分析未分析过的论文
        papers_to_analyze = []
        for p in new_papers:
            if p['title'] not in analyzed_map:
                papers_to_analyze.append(p)

        print(f"  [*] 需要分析 {len(papers_to_analyze)} 篇新论文")

        if papers_to_analyze:
            analyzed = analyze_industry_papers(industry, papers_to_analyze)
        else:
            analyzed = []

        # 合并结果（已有 + 新分析）
        final_papers = list(analyzed_map.values()) + analyzed

        # 生成报告
        report = generate_report(industry, final_papers)

        # 保存报告
        report_file = reports_dir / f"{today}_{industry.replace('/', '_')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"[+] Report saved: {report_file}")

        # 保存分析后的数据
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({'industry': industry, 'papers': final_papers, 'generated_at': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

    print("\n[+] All reports generated!")


if __name__ == '__main__':
    main()
