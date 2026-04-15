#!/usr/bin/env python3
"""
生成项目状态页面
"""

import json
import os
from datetime import datetime
from pathlib import Path


def generate_status_html():
    base_dir = Path(__file__).parent.parent

    # 统计数据
    papers_count = 0
    reports_count = 0
    analyzed_count = 0
    github_count = 0

    papers_dir = base_dir / 'papers'
    reports_dir = base_dir / 'reports'
    github_dir = base_dir / 'github'

    today = datetime.now().strftime('%Y%m%d')

    # 统计论文
    if papers_dir.exists():
        for f in papers_dir.glob('*.json'):
            if today in f.name:
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                        papers_count += len(data.get('papers', []))
                except:
                    pass

    # 统计报告
    if reports_dir.exists():
        for f in reports_dir.glob(f'{today}_*.md'):
            reports_count += 1

        for f in reports_dir.glob(f'{today}_*_data.json'):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    analyzed_count += sum(1 for p in data.get('papers', []) if p.get('analyzed'))
            except:
                pass

    # 统计 GitHub
    if github_dir.exists():
        for f in github_dir.glob(f'{today}_*.json'):
            github_count += 1

    # 获取最新日志
    log_content = ""
    logs_dir = base_dir / 'logs'
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)
        if log_files:
            try:
                log_content = log_files[0].read_text(encoding='utf-8')[-3000:]
            except:
                log_content = "无法读取日志"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paper Insight | 状态监控</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #60a5fa; margin-bottom: 2rem; font-size: 2rem; }}
        h2 {{ color: #38bdf8; margin: 1.5rem 0 1rem; font-size: 1.25rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155; }}
        .card .label {{ color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.5rem; }}
        .card .value {{ color: #f1f5f9; font-size: 2rem; font-weight: bold; }}
        .card .sub {{ color: #64748b; font-size: 0.75rem; margin-top: 0.5rem; }}
        .status {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #22c55e; margin-right: 0.5rem; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .log-box {{ background: #1e293b; border-radius: 12px; padding: 1rem; border: 1px solid #334155; font-family: 'Monaco', 'Menlo', monospace; font-size: 0.75rem; max-height: 300px; overflow-y: auto; white-space: pre-wrap; color: #94a3b8; }}
        .footer {{ margin-top: 2rem; text-align: center; color: #64748b; font-size: 0.875rem; }}
        a {{ color: #60a5fa; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .refresh {{ background: #3b82f6; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; margin-bottom: 1rem; }}
        .refresh:hover {{ background: #2563eb; }}
    </style>
    <meta http-equiv="refresh" content="30">
</head>
<body>
    <div class="container">
        <h1><span class="status"></span>Paper Insight 监控中心</h1>

        <button class="refresh" onclick="location.reload()">🔄 刷新</button>

        <div class="grid">
            <div class="card">
                <div class="label">📚 今日抓取论文</div>
                <div class="value">{papers_count}</div>
                <div class="sub">papers/ 目录</div>
            </div>
            <div class="card">
                <div class="label">✅ 已分析论文</div>
                <div class="value">{analyzed_count}</div>
                <div class="sub">reports/ 数据</div>
            </div>
            <div class="card">
                <div class="label">📊 生成报告</div>
                <div class="value">{reports_count}</div>
                <div class="sub">reports/ 目录</div>
            </div>
            <div class="card">
                <div class="label">🐙 GitHub 项目</div>
                <div class="value">{github_count}</div>
                <div class="sub">github/ 目录</div>
            </div>
        </div>

        <h2>📋 报告列表</h2>
        <div style="background: #1e293b; border-radius: 12px; padding: 1rem; border: 1px solid #334155;">
"""

    # 列出报告
    if reports_dir.exists():
        for f in sorted(reports_dir.glob(f'{today}_*.md'), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
            size = f.stat().st_size
            size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
            html += f'<div style="padding: 0.5rem; border-bottom: 1px solid #334155;"><a href="/reports/{f.name}">{f.name}</a> <span style="color: #64748b;">({size_str})</span></div>\n'
    else:
        html += '<div style="color: #64748b;">暂无报告</div>\n'

    html += f"""        </div>

        <h2>📝 实时日志</h2>
        <div class="log-box">{log_content or '暂无日志'}...</div>

        <div class="footer">
            <p>最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Paper Insight | 自动论文情报站 | <a href="/">返回首页</a></p>
        </div>
    </div>
</body>
</html>"""

    return html


def main():
    base_dir = Path(__file__).parent.parent
    status_file = base_dir / 'hugo_site' / 'public' / 'status.html'
    status_file.parent.mkdir(parents=True, exist_ok=True)

    html = generate_status_html()
    status_file.write_text(html, encoding='utf-8')
    print(f"[*] 状态页面已更新: {status_file}")


if __name__ == '__main__':
    main()
