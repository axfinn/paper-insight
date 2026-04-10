#!/usr/bin/env python3
"""
论文抓取器 - 支持多数据源和代理
- arXiv: AI/ML、新能源、半导体
- PubMed: 医疗
- Semantic Scholar: 金融、消费、游戏
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import os
from datetime import datetime
from typing import List, Dict

# 代理配置
PROXY = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY') or ''
PROXY_HANDLER = urllib.request.ProxyHandler({
    'http': PROXY,
    'https': PROXY,
}) if PROXY else urllib.request.ProxyHandler({})


def fetch_with_proxy(url: str, timeout: int = 30) -> str:
    """使用代理获取 URL 内容"""
    proxy_handler = PROXY_HANDLER
    opener = urllib.request.build_opener(proxy_handler)
    try:
        with opener.open(url, timeout=timeout) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        raise Exception(f"请求失败: {e}")


class PaperFetcher:
    def __init__(self, config_path: str = "config/industries.yaml"):
        self.config = self._load_config(config_path)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _load_config(self, config_path: str) -> dict:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def fetch_arxiv(self, categories: List[str], keywords: List[str], max_results: int = 10) -> List[Dict]:
        """从 arXiv 获取论文"""
        papers = []

        for cat in categories:
            # 构建查询
            query_parts = [f"cat:{cat}"]
            if keywords:
                query_parts.append("+OR+".join(keywords))
            query = "+AND+".join(query_parts)

            encoded_query = urllib.parse.quote(query, safe='')
            url = f"https://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

            try:
                content = fetch_with_proxy(url)
                root = ET.fromstring(content)
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

                for entry in root.findall('atom:entry', ns):
                    paper = {
                        'source': 'arXiv',
                        'id': entry.find('atom:id', ns).text,
                        'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                        'summary': entry.find('atom:summary', ns).text.strip().replace('\n', ' '),
                        'published': entry.find('atom:published', ns).text[:10],
                        'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
                        'categories': [c.get('term') for c in entry.findall('atom:category', ns)],
                        'url': entry.find('atom:id', ns).text,
                    }
                    papers.append(paper)
            except Exception as e:
                print(f"  [!] arXiv 错误 ({cat}): {e}")

            time.sleep(0.5)  # 避免请求过快

        return papers

    def fetch_pubmed(self, query: str, max_results: int = 10) -> List[Dict]:
        """从 PubMed 获取论文"""
        papers = []

        # 先搜索获取 IDs
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}&sort=date"

        try:
            content = fetch_with_proxy(search_url)
            root = ET.fromstring(content)
            ids = [id_elem.text for id_elem in root.findall('.//Id')]

            if not ids:
                return []

            # 获取详情
            fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
            content = fetch_with_proxy(fetch_url)
            data = json.loads(content)

            for id_val in ids:
                if id_val in data.get('result', {}):
                    r = data['result'][id_val]
                    paper = {
                        'source': 'PubMed',
                        'id': f"pubmed:{id_val}",
                        'title': r.get('title', ''),
                        'summary': r.get('abstract', '') or '无摘要',
                        'published': r.get('pubdate', '')[:10] if r.get('pubdate') else '',
                        'authors': [a.get('name', '') for a in r.get('authors', [])],
                        'journal': r.get('source', ''),
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{id_val}/",
                    }
                    papers.append(paper)

            time.sleep(0.5)
        except Exception as e:
            print(f"  [!] PubMed 错误: {e}")

        return papers

    def fetch_semantic_scholar(self, queries: List[str], max_results: int = 10) -> List[Dict]:
        """从 Semantic Scholar 获取论文"""
        papers = []

        for query in queries:
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={max_results}&sort=publicationDate:desc&fields=title,abstract,year,authors,journal,venue,url"

            try:
                req = urllib.request.Request(url, headers={'Accept': 'application/json'})
                content = fetch_with_proxy(url)
                data = json.loads(content)

                for item in data.get('data', []):
                    paper = {
                        'source': 'Semantic Scholar',
                        'id': item.get('paperId', ''),
                        'title': item.get('title', ''),
                        'summary': item.get('abstract', '') or '无摘要',
                        'published': str(item.get('year', '')),
                        'authors': [a.get('name', '') for a in item.get('authors', [])[:5]],
                        'journal': item.get('journal', '') or item.get('venue', ''),
                        'url': item.get('url', ''),
                    }
                    papers.append(paper)
            except Exception as e:
                print(f"  [!] Semantic Scholar 错误 ('{query}'): {e}")

            time.sleep(1)

        return papers

    def fetch_all(self) -> Dict[str, List[Dict]]:
        """抓取所有行业论文"""
        all_papers = {}

        for industry in self.config['industries']:
            name = industry['name']
            print(f"\n[*] 正在抓取 {name}...")

            papers = []
            keywords = industry.get('keywords', [])

            # arXiv
            if 'arxiv_categories' in industry:
                arxiv_papers = self.fetch_arxiv(
                    industry['arxiv_categories'],
                    keywords,
                    self.config['settings']['papers_per_industry']
                )
                papers.extend(arxiv_papers)
                print(f"    arXiv: {len(arxiv_papers)} 篇")

            # PubMed
            if 'pubmed_query' in industry:
                pubmed_papers = self.fetch_pubmed(
                    industry['pubmed_query'],
                    self.config['settings']['papers_per_industry']
                )
                papers.extend(pubmed_papers)
                print(f"    PubMed: {len(pubmed_papers)} 篇")

            # Semantic Scholar
            if 'semantic_scholar_queries' in industry:
                ss_papers = self.fetch_semantic_scholar(
                    industry['semantic_scholar_queries'],
                    self.config['settings']['papers_per_industry']
                )
                papers.extend(ss_papers)
                print(f"    Semantic Scholar: {len(ss_papers)} 篇")

            # 去重
            seen = set()
            unique_papers = []
            for p in papers:
                if p['title'] not in seen:
                    seen.add(p['title'])
                    unique_papers.append(p)

            all_papers[name] = unique_papers
            print(f"    共获取: {len(unique_papers)} 篇唯一论文")

        return all_papers

    def save_papers(self, papers: Dict[str, List[Dict]]):
        """保存论文到 JSON 文件"""
        output_dir = os.path.join(self.base_dir, 'papers')
        os.makedirs(output_dir, exist_ok=True)

        today = datetime.now().strftime('%Y%m%d')

        for industry, paper_list in papers.items():
            filename = os.path.join(output_dir, f"{today}_{industry.replace('/', '_')}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'industry': industry,
                    'fetched_at': datetime.now().isoformat(),
                    'papers': paper_list
                }, f, ensure_ascii=False, indent=2)

        print(f"\n[+] 论文已保存到 {output_dir}")


if __name__ == '__main__':
    print(f"[*] 论文抓取器启动 (代理: {PROXY or '无'})")
    fetcher = PaperFetcher()
    papers = fetcher.fetch_all()
    fetcher.save_papers(papers)
    print("\n[+] 抓取完成!")
