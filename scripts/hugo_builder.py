#!/usr/bin/env python3
"""
Hugo 网站构建器
将报告转换为 Hugo 静态网站
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


def ensure_hugo():
    """确保 Hugo 已安装"""
    import subprocess

    # 检查是否已安装
    try:
        result = subprocess.run(['hugo', 'version'], capture_output=True)
        if result.returncode == 0:
            print(f"[*] Hugo 已安装: {result.stdout.decode().strip()}")
            return True
    except:
        pass

    print("[*] 正在安装 Hugo...")

    # 检测系统架构
    import platform
    machine = platform.machine().lower()
    if 'x86_64' in machine or 'amd64' in machine:
        arch = 'amd64'
    elif 'arm64' in machine or 'aarch64' in machine:
        arch = 'arm64'
    else:
        arch = '386'

    system = platform.system().lower()
    if system == 'linux':
        ext = 'tar.gz'
    elif system == 'darwin':
        ext = 'tar.gz'
    else:
        ext = 'zip'

    version = '0.123.0'
    filename = f'hugo_{version}_{system}-{arch}.{ext}'

    url = f'https://github.com/gohugoio/hugo/releases/download/v{version}/{filename}'

    try:
        # 下载
        subprocess.run(['wget', '-q', '-O', '/tmp/hugo.tar.gz', url], check=True)
        # 解压到 /usr/local/bin
        subprocess.run(['tar', '-xzf', '/tmp/hugo.tar.gz', '-C', '/tmp'], check=True)
        subprocess.run(['mv', '/tmp/hugo', '/usr/local/bin/hugo'], check=True)
        subprocess.run(['chmod', '+x', '/usr/local/bin/hugo'], check=True)
        subprocess.run(['rm', '-f', '/tmp/hugo.tar.gz'], check=True)
        print("[✓] Hugo 安装完成")
        return True
    except Exception as e:
        print(f"[!] Hugo 安装失败: {e}")
        return False


def copy_reports_to_hugo(base_dir: Path, hugo_dir: Path):
    """将报告复制到 Hugo content 目录"""
    reports_dir = base_dir / 'reports'
    content_dir = hugo_dir / 'content' / 'reports'

    content_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime('%Y%m%d')
    count = 0

    # 复制今日报告
    for report_file in reports_dir.glob(f"{today}_*.md"):
        dest = content_dir / report_file.name
        shutil.copy2(report_file, dest)
        count += 1
        print(f"  [*] 复制: {report_file.name}")

    # 也复制最近的报告（确保网站有内容）
    for report_file in sorted(reports_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
        dest = content_dir / report_file.name
        if not dest.exists():
            shutil.copy2(report_file, dest)
            count += 1

    print(f"[+] 复制了 {count} 个报告到 Hugo")
    return count


def generate_index_page(hugo_dir: Path, reports_dir: Path):
    """生成 Hugo 首页"""
    today = datetime.now().strftime('%Y-%m-%d')

    index_content = f"""---
title: "Paper Insight | 论文情报站"
date: {today}
---

# Paper Insight 论文情报站

**自动更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 最新报告

"""

    # 收集所有报告
    all_reports = sorted(reports_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)

    categories = {
        'AI/ML': [],
        '医疗健康': [],
        '金融': [],
        '新能源': [],
        '半导体': [],
        '消费': [],
        '游戏': [],
        'GitHub': []
    }

    for r in all_reports:
        name = r.stem
        if 'github' in name.lower():
            categories['GitHub'].append(r)
        elif 'AI' in name or 'ML' in name:
            categories['AI/ML'].append(r)
        else:
            for cat in categories.keys():
                if cat in name:
                    categories[cat].append(r)
                    break

    for cat, reports in categories.items():
        if reports:
            index_content += f"\n### {cat}\n\n"
            for r in reports[:5]:
                date = datetime.fromtimestamp(r.stat().st_mtime).strftime('%m-%d')
                index_content += f"- [{r.stem}](reports/{r.name}) ({date})\n"

    index_content += f"""

## 系统状态

- **运行模式**: 持续自动抓取
- **数据来源**: arXiv, PubMed, Semantic Scholar, GitHub Trending
- **行业覆盖**: AI/ML, 医疗健康, 金融, 新能源, 半导体, 消费, 游戏

## 关于

Paper Insight 是一个自动化的论文和开源项目情报站，
利用 AI 持续分析和整理最新最有价值的技术内容。
"""

    (hugo_dir / 'content' / '_index.md').write_text(index_content, encoding='utf-8')
    print("[+] 生成 Hugo 首页")


def build_hugo_site(hugo_dir: Path):
    """构建 Hugo 网站"""
    import subprocess

    print("[*] 构建 Hugo 网站...")

    # 复制静态资源
    static_dir = hugo_dir / 'static'
    static_dir.mkdir(exist_ok=True)

    # 生成 CSS
    css_content = """
:root {
    --primary: #2563eb;
    --secondary: #7c3aed;
    --accent: #059669;
    --bg: #f8fafc;
    --text: #1e293b;
}
body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; background: var(--bg); color: var(--text); }
h1 { color: var(--primary); border-bottom: 2px solid var(--primary); padding-bottom: 0.5rem; }
h2 { color: var(--secondary); margin-top: 2rem; }
h3 { color: var(--accent); }
a { color: var(--primary); }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #e2e8f0; padding: 0.75rem; text-align: left; }
th { background: var(--primary); color: white; }
tr:nth-child(even) { background: #f1f5f9; }
blockquote { border-left: 4px solid var(--secondary); padding-left: 1rem; color: #64748b; }
code { background: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 4px; }
pre { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 8px; overflow-x: auto; }
"""
    (static_dir / 'style.css').write_text(css_content)

    # 生成 HTML 模板
    layout_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ .Title }}</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <h1>{{ .Title }}</h1>
    {{ .Content }}
    <footer style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; color: #64748b;">
        <p>Paper Insight | 自动更新的论文情报站 | 生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </footer>
</body>
</html>
"""
    (hugo_dir / 'layouts' / '_default' / 'single.html').parent.mkdir(parents=True, exist_ok=True)
    (hugo_dir / 'layouts' / '_default' / 'single.html').write_text(layout_html)

    # 复制 hugo.toml
    hugo_config = """baseURL = "http://localhost:8084/"
languageCode = "zh-cn"
title = "Paper Insight | 论文情报站"
publishDir = "public"
disableHugoGeneratorInject = true

[frontmatter]
date = ["date", "publishDate"]
"""
    (hugo_dir / 'hugo.toml').write_text(hugo_config)

    # 运行 hugo
    result = subprocess.run(
        ['hugo', '--destination', 'public'],
        cwd=hugo_dir,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("[✓] Hugo 网站构建成功")
        return True
    else:
        print(f"[!] Hugo 构建失败: {result.stderr}")
        return False


def main():
    base_dir = Path(__file__).parent.parent
    hugo_dir = base_dir / 'hugo_site'

    print(f"\n[*] 构建 Hugo 网站...")

    # 确保 Hugo
    if not ensure_hugo():
        print("[!] Hugo 安装失败，跳过网站构建")
        return

    # 复制报告
    reports_dir = base_dir / 'reports'
    copy_reports_to_hugo(base_dir, hugo_dir)

    # 生成首页
    generate_index_page(hugo_dir, reports_dir)

    # 构建
    if build_hugo_site(hugo_dir):
        print(f"\n[✓] 网站构建完成: {hugo_dir / 'public'}")

        # 生成状态页面
        try:
            from status_page import main as update_status
            update_status()
        except Exception as e:
            print(f"  [!] 状态页面更新失败: {e}")


if __name__ == '__main__':
    main()
