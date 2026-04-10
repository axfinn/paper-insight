#!/usr/bin/env python3
"""
Paper Insight 主运行器
- 持续运行，自动抓取、分析、生成报告
- 支持自迭代：定期回顾分析质量并改进
"""

import os
import sys
import time
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread

# 导入本地模块
from paper_fetcher import PaperFetcher
from paper_analyzer import analyze_industry_papers, generate_report

class PaperInsightRunner:
    def __init__(self, config_path: str = "config/industries.yaml"):
        self.config_path = config_path
        self.base_dir = Path(__file__).parent.parent
        self.papers_dir = self.base_dir / 'papers'
        self.reports_dir = self.base_dir / 'reports'
        self.state_file = self.base_dir / 'data' / 'state.json'

        # 确保目录存在
        for d in [self.papers_dir, self.reports_dir, self.base_dir / 'data']:
            d.mkdir(exist_ok=True)

        self.state = self.load_state()

    def load_state(self) -> dict:
        """加载运行状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'last_fetch': None,
            'last_analysis': None,
            'iteration': 0,
            'improvements': [],
            'industry_status': {}
        }

    def save_state(self):
        """保存运行状态"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def fetch_all(self) -> dict:
        """抓取所有行业论文"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [*] Fetching papers...")
        fetcher = PaperFetcher(self.config_path)
        papers = fetcher.fetch_all()
        fetcher.save_papers(papers)
        self.state['last_fetch'] = datetime.now().isoformat()
        self.save_state()
        return papers

    def analyze_all(self, papers: dict):
        """分析所有论文"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [*] Analyzing papers...")
        reports_dir = self.reports_dir
        reports_dir.mkdir(exist_ok=True)

        for industry, paper_list in papers.items():
            print(f"\n[*] Analyzing {industry}...")
            analyzed = analyze_industry_papers(industry, paper_list)
            report = generate_report(industry, analyzed)

            # 保存报告
            today = datetime.now().strftime('%Y%m%d')
            report_file = reports_dir / f"{today}_{industry.replace('/', '_')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            # 保存分析数据
            data_file = reports_dir / f"{today}_{industry.replace('/', '_')}_data.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({'industry': industry, 'papers': analyzed, 'generated_at': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

            print(f"[+] {industry}: {len(analyzed)} papers analyzed")

        self.state['last_analysis'] = datetime.now().isoformat()
        self.state['iteration'] += 1
        self.save_state()

    def self_improve(self):
        """自迭代：分析过往表现，改进策略"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [*] Self-improvement check...")

        # 读取最近的分析结果
        recent_files = sorted(self.reports_dir.glob("*_data.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:7]

        if len(recent_files) < 3:
            print("[*] Not enough data for self-improvement")
            return

        # 统计各行业的分析情况
        stats = {}
        for f in recent_files:
            with open(f, 'r') as fp:
                data = json.load(fp)
                industry = data['industry']
                if industry not in stats:
                    stats[industry] = {'total': 0, 'analyzed': 0, 'avg_rating': 0}
                for paper in data['papers']:
                    stats[industry]['total'] += 1
                    if paper.get('analyzed'):
                        stats[industry]['analyzed'] += 1
                        stats[industry]['avg_rating'] += paper.get('rating', 0)

        # 计算改进建议
        improvements = []
        for industry, s in stats.items():
            if s['total'] > 0:
                success_rate = s['analyzed'] / s['total'] * 100
                avg_rating = s['avg_rating'] / s['analyzed'] if s['analyzed'] > 0 else 0
                improvements.append(f"{industry}: 分析成功率 {success_rate:.0f}%, 平均评分 {avg_rating:.1f}/5")

        self.state['improvements'].append({
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'iteration': self.state['iteration']
        })

        # 只保留最近 100 条改进记录
        self.state['improvements'] = self.state['improvements'][-100:]

        self.save_state()
        print(f"[+] Self-improvement complete. {len(improvements)} industries tracked.")

    def generate_homepage(self):
        """生成首页索引"""
        today = datetime.now().strftime('%Y%m%d')
        reports_dir = self.reports_dir

        homepage = f"""# Paper Insight | 论文情报站

**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**运行迭代**: {self.state['iteration']} 次

## 今日报告

"""

        for report_file in sorted(reports_dir.glob(f"{today}_*.md")):
            industry = report_file.stem.replace(f"{today}_", "").replace('_', '/')
            homepage += f"- [{industry}]({report_file.name})\n"

        if not list(reports_dir.glob(f"{today}_*.md")):
            homepage += "_暂无今日报告_\n"

        homepage += """

## 行业分类

"""

        # 读取配置获取行业列表
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        for industry in config['industries']:
            name = industry['name']
            # 找最新的报告
            latest = sorted(reports_dir.glob(f"*_{name.replace('/', '_')}.md"), key=lambda x: x.stat().st_mtime, reverse=True)
            if latest:
                homepage += f"- [{name}]({latest[0].name})\n"
            else:
                homepage += f"- {name} _(暂无报告)_\n"

        homepage += f"""

## 运行状态

- **抓取时间**: {self.state.get('last_fetch', '从未抓取')}
- **分析时间**: {self.state.get('last_analysis', '从未分析')}
- **迭代次数**: {self.state['iteration']}

## 最近改进

"""
        for imp in self.state['improvements'][-5:]:
            homepage += f"- [{imp['timestamp'][:10]}] 迭代 {imp['iteration']}: {len(imp['stats'])} 个行业\n"

        if not self.state['improvements']:
            homepage += "_暂无改进记录_\n"

        # 保存首页
        index_file = self.base_dir / 'README.md'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(homepage)

        print(f"[+] Homepage updated: {index_file}")

    def run_cycle(self):
        """运行一个完整周期"""
        try:
            # 1. 抓取
            papers = self.fetch_all()

            # 2. 分析
            self.analyze_all(papers)

            # 3. 生成首页
            self.generate_homepage()

            # 4. 自迭代检查（每10次迭代执行一次）
            if self.state['iteration'] % 10 == 0:
                self.self_improve()

        except Exception as e:
            print(f"[!] Error in run_cycle: {e}")
            import traceback
            traceback.print_exc()

    def run_continuous(self, fetch_interval: int = 3600, analysis_interval: int = 1800):
        """
        持续运行模式
        - fetch_interval: 抓取间隔（秒），默认 1 小时
        - analysis_interval: 分析间隔（秒），默认 30 分钟
        """
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Paper Insight Runner                       ║
║                                                              ║
║  抓取间隔: {fetch_interval} 秒 ({(fetch_interval/3600):.1f} 小时)                         ║
║  分析间隔: {analysis_interval} 秒 ({(analysis_interval/60):.0f} 分钟)                       ║
║                                                              ║
║  持续运行中... 按 Ctrl+C 停止                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)

        last_fetch = None
        last_analysis = None

        while True:
            now = datetime.now()

            # 检查是否需要抓取
            if last_fetch is None or (now - last_fetch).total_seconds() >= fetch_interval:
                print(f"\n[{now.strftime('%H:%M:%S')}] === Fetch Cycle ===")
                self.fetch_all()
                last_fetch = now

            # 检查是否需要分析
            if last_analysis is None or (now - last_analysis).total_seconds() >= analysis_interval:
                print(f"\n[{now.strftime('%H:%M:%S')}] === Analysis Cycle ===")
                papers_dir = self.papers_dir
                today = datetime.now().strftime('%Y%m%d')

                # 读取今日未分析的论文
                for paper_file in papers_dir.glob(f"{today}_*.json"):
                    with open(paper_file, 'r') as f:
                        data = json.load(f)
                    self.analyze_all({data['industry']: data['papers']})

                last_analysis = now

            # 等待一段时间
            time.sleep(60)  # 每分钟检查一次


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Paper Insight Runner')
    parser.add_argument('--once', action='store_true', help='运行一次后退出')
    parser.add_argument('--fetch-interval', type=int, default=3600, help='抓取间隔（秒）')
    parser.add_argument('--analysis-interval', type=int', default=1800, help='分析间隔（秒）')

    args = parser.parse_args()

    runner = PaperInsightRunner()

    if args.once:
        runner.run_cycle()
    else:
        runner.run_continuous(args.fetch_interval, args.analysis_interval)


if __name__ == '__main__':
    main()
