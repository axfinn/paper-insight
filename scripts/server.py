#!/usr/bin/env python3
"""
Paper Insight HTTP 服务器
同时服务静态文件和动态状态页面
"""

import http.server
import socketserver
import os
from pathlib import Path
import sys

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from status_page import generate_status_html


class PaperInsightHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status' or self.path == '/status.html':
            # 生成动态状态页面
            html = generate_status_html()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            # 其他请求走静态文件
            super().do_GET()

    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"  [{self.log_date_time_string()}] {args[0]}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Paper Insight HTTP Server')
    parser.add_argument('--port', default=8084, type=int, help='Port to listen on')
    parser.add_argument('--directory', default=None, help='Directory to serve')

    args = parser.parse_args()

    # 获取目录
    if args.directory:
        base_dir = Path(args.directory)
    else:
        base_dir = Path(__file__).parent.parent / 'hugo_site' / 'public'

    os.chdir(base_dir)

    print(f"[*] Paper Insight 服务器启动")
    print(f"[*] 端口: {args.port}")
    print(f"[*] 目录: {base_dir}")
    print(f"[*] 状态页: http://localhost:{args.port}/status")

    with socketserver.TCPServer(("", args.port), PaperInsightHandler) as httpd:
        print(f"[*] 服务运行中，按 Ctrl+C 停止")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] 服务器停止")


if __name__ == '__main__':
    main()
