#!/usr/bin/env python3
"""
代理配置模块
- 支持 HTTP/SOCKS5 代理
- 自动检测网络，失败时切换代理
"""

import os
import socket
from typing import Optional

# 尝试导入 socks（如果没有就用 HTTP 代理）
try:
    import socks
    HAS_PYSOCKS = True
except ImportError:
    HAS_PYSOCKS = False


class ProxyConfig:
    """代理配置"""

    def __init__(self, config_path: str = None):
        self.enabled = False
        self.proxy_type = 'socks5'  # socks5 或 http
        self.host = '127.0.0.1'
        self.port = 1080

        # 尝试加载本地配置
        if config_path:
            self._load_config(config_path)
        else:
            # 尝试从环境变量和默认路径加载
            self._load_from_env()
            self._load_from_file()

    def _load_from_env(self):
        """从环境变量加载"""
        if os.environ.get('PROXY_ENABLED', '').lower() == 'true':
            self.enabled = True
        if os.environ.get('PROXY_HOST'):
            self.host = os.environ['PROXY_HOST']
        if os.environ.get('PROXY_PORT'):
            self.port = int(os.environ['PROXY_PORT'])
        if os.environ.get('PROXY_TYPE'):
            self.proxy_type = os.environ['PROXY_TYPE']

    def _load_from_file(self):
        """从配置文件加载"""
        config_paths = [
            'config/local.yaml',
            os.path.expanduser('~/.paper-insight/proxy.yaml'),
        ]
        import yaml
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        cfg = yaml.safe_load(f)
                    if cfg and 'proxy' in cfg:
                        p = cfg['proxy']
                        self.enabled = p.get('enabled', False)
                        self.proxy_type = p.get('type', 'socks5')
                        self.host = p.get('host', '127.0.0.1')
                        self.port = p.get('port', 1080)
                except:
                    pass
                break

    def __str__(self):
        if not self.enabled:
            return "无代理"
        return f"{self.proxy_type}://{self.host}:{self.port}"


def check_connection(host: str = 'arxiv.org', port: int = 443, timeout: float = 3.0) -> bool:
    """检测网络连接，返回 True 表示可达"""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, socket.error, OSError):
        return False


def create_proxy_opener(proxy_config: ProxyConfig):
    """根据配置创建代理 opener"""
    if not proxy_config.enabled:
        return None

    if proxy_config.proxy_type == 'socks5' and HAS_PYSOCKS:
        return socks.socksocket()
    elif proxy_config.proxy_type == 'http':
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({
            'http': f"http://{proxy_config.host}:{proxy_config.port}",
            'https': f"http://{proxy_config.host}:{proxy_config.port}",
        })
        return urllib.request.build_opener(proxy_handler)

    return None


# 全局代理配置实例
_proxy_config = None

def get_proxy_config() -> ProxyConfig:
    global _proxy_config
    if _proxy_config is None:
        _proxy_config = ProxyConfig()
    return _proxy_config


def fetch_with_fallback(url: str, headers: dict = None, timeout: int = 30, use_proxy: bool = True) -> tuple:
    """
    获取 URL 内容，失败时自动尝试代理
    返回 (content, used_proxy, error)
    """
    import urllib.request

    config = get_proxy_config()

    # 先尝试直接连接
    if check_connection():
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8'), False, None
        except Exception as e:
            print(f"    [!] 直接连接失败: {e}，尝试代理...")

    # 失败后尝试代理
    if use_proxy and config.enabled:
        try:
            if config.proxy_type == 'socks5' and HAS_PYSOCKS:
                sock = socks.socksocket()
                sock.set_proxy(socks.SOCKS5, config.host, config.port)
                sock.settimeout(timeout)
                sock.connect(('arxiv.org', 443))

                # 简单 HTTP GET
                req = '\r\n'.join([
                    f'GET {url} HTTP/1.1',
                    f'Host: arxiv.org',
                    'User-Agent: Mozilla/5.0',
                    'Connection: close',
                    '', ''
                ])
                sock.send(req.encode())

                # 读取响应
                response = b''
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if b'\r\n\r\n' in response:
                        break

                sock.close()

                # 简单的响应解析
                if response:
                    # 去掉 HTTP 头
                    parts = response.split(b'\r\n\r\n', 1)
                    if len(parts) > 1:
                        return parts[1].decode('utf-8', errors='ignore'), True, None

            elif config.proxy_type == 'http':
                import urllib.request
                proxy_handler = urllib.request.ProxyHandler({
                    'http': f"http://{config.host}:{config.port}",
                    'https': f"http://{config.host}:{config.port}",
                })
                opener = urllib.request.build_opener(proxy_handler)
                req = urllib.request.Request(url, headers=headers or {})
                with opener.open(req, timeout=timeout) as response:
                    return response.read().decode('utf-8'), True, None

        except Exception as e:
            return None, True, str(e)

    return None, False, "无法连接网络且代理不可用"


if __name__ == '__main__':
    config = get_proxy_config()
    print(f"代理配置: {config}")

    # 测试连接
    online = check_connection()
    print(f"网络状态: {'在线' if online else '离线'}")
