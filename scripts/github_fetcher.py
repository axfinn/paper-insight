#!/usr/bin/env python3
"""
GitHub Trending 项目爬虫
爬取 GitHub Trending 页面，按语言分类，发现有意思的开源项目
"""

import urllib.request
import urllib.parse
import json
import re
import time
from datetime import datetime
from typing import List, Dict

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class GitHubFetcher:
    """GitHub Trending 爬虫"""

    # 支持的语言分类
    LANGUAGES = {
        'all': '',
        'python': 'Python',
        'javascript': 'JavaScript',
        'go': 'Go',
        'rust': 'Rust',
        'java': 'Java',
        'typescript': 'TypeScript',
        'c': 'C',
        'cpp': 'C++',
        'ruby': 'Ruby',
        'swift': 'Swift',
        'kotlin': 'Kotlin',
    }

    # 不想看的语言/分类
    EXCLUDE_LANGS = ['Jupyter Notebook']  # .ipynb 文件太多

    def __init__(self, token: str = None):
        self.token = token or self._get_token()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/vnd.github.v3+json',
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'

    def _get_token(self) -> str:
        """从环境变量获取 GitHub Token"""
        import os
        return os.environ.get('GITHUB_TOKEN', '')

    def fetch_trending(self, language: str = 'all', since: str = 'daily') -> List[Dict]:
        """
        获取 GitHub Trending

        Args:
            language: 编程语言 (python, go, rust, ...)
            since: 时间范围 (daily, weekly, monthly)

        Returns:
            项目列表
        """
        if not HAS_BS4:
            print("[!] beautifulsoup4 not installed, using GitHub API instead")
            return self.fetch_via_api(language, since)

        url = f"https://github.com/trending"
        if language and language != 'all':
            url += f"/{language}"
        url += f"?since={since}"

        projects = []

        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')

            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.select('article.Box-row')

            for article in articles:
                # 项目名
                repo_link = article.select_one('h2 a')
                if not repo_link:
                    continue

                full_name = repo_link.get('href', '').strip('/')  # e.g. "owner/repo"
                parts = full_name.split('/')
                if len(parts) != 2:
                    continue

                owner, repo = parts

                # 描述
                desc_elem = article.select_one('p')
                description = desc_elem.get_text().strip() if desc_elem else ''

                # 编程语言
                lang_elem = article.select_one('[itemprop="programmingLanguage"]')
                prog_lang = lang_elem.get_text().strip() if lang_elem else ''

                # 跳过不想要的语言
                if prog_lang in self.EXCLUDE_LANGS:
                    continue

                # 星标数
                stars = ''
                star_elem = article.select_one('a[href*="/stargazers"]')
                if star_elem:
                    stars = star_elem.get_text().strip()

                # 今日新增
                today_stars = ''
                for span in article.select('span'):
                    text = span.get_text().strip()
                    if 'today' in text.lower():
                        today_stars = text
                        break

                # 英文判断
                is_english = self._is_english_description(description)

                project = {
                    'owner': owner,
                    'repo': repo,
                    'full_name': full_name,
                    'description': description,
                    'language': prog_lang,
                    'stars': stars,
                    'today_stars': today_stars,
                    'url': f"https://github.com/{full_name}",
                    'fetched_at': datetime.now().isoformat(),
                    'is_english': is_english,
                }
                projects.append(project)

        except Exception as e:
            print(f"[!] GitHub trending error: {e}")

        return projects

    def fetch_via_api(self, language: str = 'all', since: str = 'daily') -> List[Dict]:
        """通过 GitHub API 获取 Trending（需要 Token）"""
        if not self.token:
            print("[!] No GitHub token, cannot use API")
            return []

        # 计算日期范围
        days = {'daily': 1, 'weekly': 7, 'monthly': 30}.get(since, 1)
        date_range = f"created:>{datetime.now().strftime('%Y-%m-%d')}"

        # 构建搜索查询
        query = f"{date_range}"
        if language and language != 'all':
            lang_name = self.LANGUAGES.get(language, language)
            query += f" language:{lang_name}"

        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page=30"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read())

            projects = []
            for item in data.get('items', []):
                project = {
                    'owner': item.get('owner', {}).get('login', ''),
                    'repo': item.get('name', ''),
                    'full_name': item.get('full_name', ''),
                    'description': item.get('description', '') or '',
                    'language': item.get('language', '') or '',
                    'stars': str(item.get('stargazers_count', 0)),
                    'today_stars': f"{item.get('stargazers_count', 0)} stars (total)",
                    'url': item.get('html_url', ''),
                    'fetched_at': datetime.now().isoformat(),
                    'is_english': self._is_english_description(item.get('description', '')),
                }
                projects.append(project)

            return projects

        except Exception as e:
            print(f"[!] GitHub API error: {e}")
            return []

    def _is_english_description(self, text: str) -> bool:
        """简单判断描述是否是英文"""
        if not text:
            return False
        # 检查是否包含中文字符
        chinese = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese) == 0

    def fetch_all_languages(self, since: str = 'daily') -> Dict[str, List[Dict]]:
        """获取所有主要语言的 Trending"""
        all_projects = {}

        # 重点关注的语言
        focus_langs = ['python', 'go', 'rust', 'typescript', 'javascript']

        for lang in focus_langs:
            print(f"[*] Fetching GitHub trending: {lang}...")
            projects = self.fetch_trending(language=lang, since=since)
            all_projects[lang] = projects
            print(f"    Found {len(projects)} projects")
            time.sleep(2)  # 避免请求过快

        # 也获取总览
        print(f"[*] Fetching GitHub trending: all...")
        all_projects['all'] = self.fetch_trending(language='all', since=since)
        print(f"    Found {len(all_projects['all'])} projects")

        return all_projects

    def save_projects(self, projects: Dict[str, List[Dict]]):
        """保存项目到 JSON 文件"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, 'github')
        os.makedirs(output_dir, exist_ok=True)

        today = datetime.now().strftime('%Y%m%d')

        for lang, project_list in projects.items():
            filename = os.path.join(output_dir, f"{today}_{lang}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'language': lang,
                    'fetched_at': datetime.now().isoformat(),
                    'projects': project_list
                }, f, ensure_ascii=False, indent=2)

        print(f"[+] Saved GitHub projects to {output_dir}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='GitHub Trending Fetcher')
    parser.add_argument('--lang', default='all', help='Language (python, go, rust, ...)')
    parser.add_argument('--since', default='daily', help='Time range (daily, weekly, monthly)')
    parser.add_argument('--all', action='store_true', help='Fetch all languages')

    args = parser.parse_args()

    fetcher = GitHubFetcher()

    if args.all:
        projects = fetcher.fetch_all_languages(args.since)
    else:
        projects = {args.lang: fetcher.fetch_trending(args.lang, args.since)}

    fetcher.save_projects(projects)

    # 打印摘要
    for lang, plist in projects.items():
        print(f"\n{lang}: {len(plist)} projects")
        for p in plist[:3]:
            print(f"  - {p['full_name']}: {p['description'][:50]}...")


if __name__ == '__main__':
    main()
