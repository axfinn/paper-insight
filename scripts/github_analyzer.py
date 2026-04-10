#!/usr/bin/env python3
"""
GitHub 项目 AI 分析器
分析 Trending 项目的创新点、技术栈、应用场景，生成排行榜报告
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def analyze_project(project: dict, api_key: str = None) -> dict:
    """使用 Claude 分析单个项目"""
    if not HAS_ANTHROPIC:
        return {**project, 'analyzed': False, 'error': 'anthropic not installed'}

    client = anthropic.Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))

    prompt = f"""你是一位资深开源项目评审专家。请分析以下 GitHub 项目，判断它是否"有意思"。

项目: {project.get('full_name', 'N/A')}
描述: {project.get('description', 'N/A')}
语言: {project.get('language', 'N/A')}
总星标: {project.get('stars', 'N/A')}
今日新增: {project.get('today_stars', 'N/A')}
链接: {project.get('url', 'N/A')}

请分析并返回以下信息（JSON格式）：
{{
    "title": "项目名称",
    "innovation": "核心创新点（20字内）",
    "tech_stack": ["技术栈1", "技术栈2"],
    "application": "典型应用场景",
    "why_interesting": "为什么这个项目有意思（50字内）",
    "potential": "潜力评分 1-5",
    "difficulty": "学习难度 1-5（1=入门, 5=专家）",
    "category": "项目分类（如：AI工具、DevOps、前端框架、数据库、安全等）",
    "verdict": "值得关注的理由或不值得关注的原因（30字内）"
}}

只返回JSON，不要其他内容。"""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.content[0].text)
        return {**project, **result, 'analyzed': True}
    except Exception as e:
        return {**project, 'analyzed': False, 'error': str(e)}


def analyze_projects(projects: list, api_key: str = None) -> list:
    """分析项目列表"""
    analyzed = []

    for i, project in enumerate(projects):
        print(f"  Analyzing [{i+1}/{len(projects)}]: {project.get('full_name', '')}")
        result = analyze_project(project, api_key)
        analyzed.append(result)

    return analyzed


def generate_ranking_report(lang: str, projects: list, analyzed: list) -> str:
    """生成排行榜报告"""

    # 按潜力排序
    sorted_projects = sorted(analyzed, key=lambda x: x.get('potential', 0), reverse=True)

    report = f"""# GitHub Trending {lang.upper()} 排行榜

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析项目**: {len(analyzed)} 个
**数据来源**: GitHub Trending (daily)

---

## 🏆 TOP 10 最值得关注的项目

"""

    for i, p in enumerate(sorted_projects[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"

        report += f"""### {medal} {p.get('full_name', 'N/A')}

**评分**: {'⭐' * p.get('potential', 0)} ({p.get('potential', 0)}/5) | **难度**: {'🔒' * p.get('difficulty', 0)} ({p.get('difficulty', 0)}/5)
**语言**: {p.get('language', 'N/A')} | **分类**: {p.get('category', 'N/A')}
**今日新增**: {p.get('today_stars', 'N/A')} | **总星标**: {p.get('stars', 'N/A')}

**描述**: {p.get('description', 'N/A')}

**创新点**: {p.get('innovation', 'N/A')}

**技术栈**: {', '.join(p.get('tech_stack', [])[:5])}

**应用场景**: {p.get('application', 'N/A')}

**为什么有意思**: {p.get('why_interesting', 'N/A')}

**结论**: {p.get('verdict', 'N/A')}

[GitHub 链接]({p.get('url', '#')})

---

"""

    # 分类统计
    categories = {}
    for p in analyzed:
        cat = p.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + 1

    report += f"""## 📊 分类统计

"""

    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{cat}**: {count} 个项目\n"

    # 编程语言分布
    langs = {}
    for p in analyzed:
        lang = p.get('language', 'Unknown')
        langs[lang] = langs.get(lang, 0) + 1

    report += f"""
## 📈 语言分布

"""

    for lang_name, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{lang_name}**: {count} 个项目\n"

    # 未分析的项目
    failed = [p for p in analyzed if not p.get('analyzed')]
    if failed:
        report += f"""
## ⚠️ 未分析的项目 ({len(failed)} 个)

"""
        for p in failed[:10]:
            report += f"- [{p.get('full_name')}]({p.get('url')}) - {p.get('language', 'N/A')}\n"

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description='GitHub Project Analyzer')
    parser.add_argument('--lang', default='all', help='Language (python, go, rust, ... or all)')
    parser.add_argument('--input-dir', default='github', help='Input directory with fetched projects')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / 'reports'
    output_dir.mkdir(exist_ok=True)

    # 读取数据
    today = datetime.now().strftime('%Y%m%d')

    if args.lang == 'all':
        langs = ['python', 'go', 'rust', 'typescript', 'javascript', 'all']
    else:
        langs = [args.lang]

    for lang in langs:
        input_file = input_dir / f"{today}_{lang}.json"
        if not input_file.exists():
            print(f"[!] No data file for {lang}: {input_file}")
            continue

        print(f"\n[*] Analyzing {lang}...")

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        projects = data.get('projects', [])

        if not projects:
            print(f"    No projects found")
            continue

        # 分析项目
        analyzed = analyze_projects(projects)

        # 生成报告
        report = generate_ranking_report(lang, projects, analyzed)

        # 保存报告
        report_file = output_dir / f"{today}_github_{lang}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"[+] Report saved: {report_file}")


if __name__ == '__main__':
    main()
