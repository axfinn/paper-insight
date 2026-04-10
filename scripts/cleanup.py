#!/usr/bin/env python3
"""
磁盘清理脚本 - 自动清理旧数据，防止磁盘爆满
保留策略：
- 论文数据：最近 7 天
- GitHub 数据：最近 7 天
- 报告：最近 30 天（更重要的数据）
- 日志：最近 3 天
"""

import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path


def get_days_old(file_path: Path) -> int:
    """获取文件年龄（天）"""
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return (datetime.now() - mtime).days


def cleanup_directory(dir_path: Path, keep_days: int, pattern: str = "*"):
    """清理目录中过期的文件"""
    if not dir_path.exists():
        return 0

    removed = 0
    for f in dir_path.glob(pattern):
        if f.is_file():
            age = get_days_old(f)
            if age > keep_days:
                f.unlink()
                print(f"  🗑️  删除 ({age}天前): {f.name}")
                removed += 1
        elif f.is_dir():
            age = get_days_old(f)
            if age > keep_days:
                shutil.rmtree(f)
                print(f"  🗑️  删除目录 ({age}天前): {f.name}")
                removed += 1
    return removed


def cleanup_autodev_logs(keep_days: int = 3):
    """清理 autodev 的旧项目（保留最近活跃的）"""
    removed = 0

    # 清理 /tmp/autodev
    autodev_base = Path("/tmp/autodev")
    if autodev_base.exists():
        for project_dir in autodev_base.iterdir():
            if not project_dir.is_dir():
                continue
            age = get_days_old(project_dir)
            if age > keep_days:
                shutil.rmtree(project_dir)
                print(f"  🗑️  删除 autodev 项目 ({age}天前): {project_dir.name}")
                removed += 1

    # 清理本地的 autodev_workspace
    script_dir = Path(__file__).parent.parent
    local_workspace = script_dir / 'autodev_workspace'
    if local_workspace.exists():
        for project_dir in local_workspace.iterdir():
            if not project_dir.is_dir():
                continue
            age = get_days_old(project_dir)
            if age > keep_days:
                shutil.rmtree(project_dir)
                print(f"  🗑️  删除本地 autodev 项目 ({age}天前): {project_dir.name}")
                removed += 1

    return removed


def cleanup_tmp(keep_days: int = 1):
    """清理 /tmp 下相关的临时文件"""
    tmp_dir = Path("/tmp")
    removed = 0

    # 清理 python 缓存
    for pattern in ["**/__pycache__", "**/*.pyc", "**/*.pyo"]:
        for f in tmp_dir.glob(pattern):
            try:
                if f.is_file():
                    f.unlink()
                    removed += 1
                elif f.is_dir():
                    shutil.rmtree(f)
                    removed += 1
            except:
                pass

    return removed


def main():
    base_dir = Path(__file__).parent.parent
    print(f"\n{'='*60}")
    print(f"🧹 Paper Insight 磁盘清理")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   根目录: {base_dir}")
    print('='*60)

    total_removed = 0

    # 论文数据 - 保留 7 天
    papers_dir = base_dir / 'papers'
    n = cleanup_directory(papers_dir, keep_days=7)
    print(f"  论文数据: 删除 {n} 个过期文件")
    total_removed += n

    # GitHub 数据 - 保留 7 天
    github_dir = base_dir / 'github'
    n = cleanup_directory(github_dir, keep_days=7)
    print(f"  GitHub 数据: 删除 {n} 个过期文件")
    total_removed += n

    # 报告 - 保留 30 天（更重要）
    reports_dir = base_dir / 'reports'
    n = cleanup_directory(reports_dir, keep_days=30)
    print(f"  报告: 删除 {n} 个过期文件")
    total_removed += n

    # 日志 - 保留 3 天
    logs_dir = base_dir / 'logs'
    n = cleanup_directory(logs_dir, keep_days=3)
    print(f"  日志: 删除 {n} 个过期文件")
    total_removed += n

    # autodev 项目 - 保留 3 天
    n = cleanup_autodev_logs(keep_days=3)
    print(f"  autodev 项目: 清理 {n} 个过期项目")
    total_removed += n

    # /tmp 清理
    n = cleanup_tmp()
    print(f"  临时文件: 清理 {n} 个缓存")

    # 统计磁盘使用
    try:
        import subprocess
        result = subprocess.run(['df', '-h', str(base_dir)],
                              capture_output=True, text=True)
        print(f"\n📊 磁盘使用:")
        for line in result.stdout.split('\n'):
            if line.startswith('/'):
                print(f"   {line}")
    except:
        pass

    print(f"\n✅ 清理完成，共删除 {total_removed} 个项目")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
